import os
import tempfile
import threading

import cv2
import numpy as np
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from camera.models import Camera
from parking.consumers import VideoFeedConsumer
from parking.models import Parking, ParkingMembership, Zone
from users.models import User
from . import events
from .geometry import crop_size, order_corners
from .worker import ZoneConfig, ZoneWorker, detect, load_zones, spot_transforms

SQUARE = [[10, 10], [60, 10], [60, 60], [10, 60]]


def write_video(path, frames=10):
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
    for i in range(frames):
        writer.write(np.full((48, 64, 3), i * 20, np.uint8))
    writer.release()


class GeometryTests(SimpleTestCase):
    def test_corners_are_ordered_clockwise_from_top_left(self):
        rect = order_corners([[60, 60], [10, 10], [60, 10], [10, 60]])
        self.assertEqual(rect.tolist(), SQUARE)

    def test_crop_never_exceeds_the_frame(self):
        rect = order_corners([[0, 0], [30000, 0], [30000, 30000], [0, 30000]])
        self.assertEqual(crop_size(rect, (48, 64, 3)), (64, 48))

    def test_detect_reports_each_spot_in_layout_order(self):
        transforms = spot_transforms({"B": SQUARE, "A": SQUARE})
        message = detect(np.zeros((80, 80, 3), np.uint8), 3, transforms, lambda crops: ["empty", "occupied"])
        self.assertEqual(message, {
            "area": 3,
            "available_spots": 1,
            "spot_details": [{"spot": "B", "status": "empty"}, {"spot": "A", "status": "occupied"}],
        })

    def test_classifier_failure_marks_spots_as_error(self):
        def broken(crops):
            raise OSError("model server down")

        message = detect(np.zeros((80, 80, 3), np.uint8), 1, spot_transforms({"A": SQUARE}), broken)
        self.assertEqual(message["spot_details"], [{"spot": "A", "status": "error"}])


class ZoneLoadingTests(TestCase):
    def test_only_zones_with_spots_and_a_camera_are_watched(self):
        parking = Parking.objects.create(name="A")
        Zone.objects.create(parking=parking, number=1, spots={"P2": SQUARE, "P1": SQUARE})
        Zone.objects.create(parking=parking, number=2, spots={"P1": SQUARE})
        Zone.objects.create(parking=parking, number=3, spots={})
        Camera.objects.create(parking=parking, area=1, path="cam-1.mp4", ref="C1")
        Camera.objects.create(parking=parking, area=3, path="cam-3.mp4", ref="C3")

        configs = load_zones()

        self.assertEqual([(c.area, c.path, [n for n, _ in c.spots]) for c in configs], [(1, "cam-1.mp4", ["P2", "P1"])])

    def test_shards_split_the_zones(self):
        parking = Parking.objects.create(name="A")
        for number in range(1, 9):
            Zone.objects.create(parking=parking, number=number, spots={"P1": SQUARE})
            Camera.objects.create(parking=parking, area=number, path=f"cam-{number}.mp4", ref="C")
        shards = [{c.area for c in load_zones(i, 3)} for i in range(3)]
        self.assertEqual(set().union(*shards), set(range(1, 9)))
        self.assertEqual(sum(len(s) for s in shards), 8)


class ZoneWorkerTests(SimpleTestCase):
    def test_worker_publishes_the_zone_occupancy(self):
        path = os.path.join(tempfile.mkdtemp(), "lot.avi")
        write_video(path)
        published = []
        done = threading.Event()

        def publish(parking_id, area, message):
            published.append((parking_id, area, message))
            done.set()

        config = ZoneConfig("p1", 4, path, (("A", tuple(map(tuple, SQUARE))),))
        worker = ZoneWorker(config, publish=publish, classifier=lambda crops: ["empty"] * len(crops))
        worker.start()
        self.assertTrue(done.wait(5))
        worker.stop()
        worker.join(5)

        self.assertEqual(published[0], ("p1", 4, {"area": 4, "available_spots": 1, "spot_details": [{"spot": "A", "status": "empty"}]}))


class VideoFeedConsumerTests(TransactionTestCase):
    def setUp(self):
        self.parking = Parking.objects.create(name="A")
        self.operator = User.objects.create_user(username="operator")
        ParkingMembership.objects.create(user=self.operator, parking=self.parking, role="operator")
        Zone.objects.create(parking=self.parking, number=1, spots={"P1": SQUARE})
        Camera.objects.create(parking=self.parking, area=1, path="cam.mp4", ref="C")

    def connect(self, user):
        communicator = WebsocketCommunicator(VideoFeedConsumer.as_asgi(), "/ws/video/1/")
        communicator.scope["user"] = user
        communicator.scope["url_route"] = {"kwargs": {"area": "1"}}
        return communicator

    def test_members_receive_published_occupancy_until_removed(self):
        message = {"area": 1, "available_spots": 1, "spot_details": [{"spot": "P1", "status": "empty"}]}
        group = events.zone_group(self.parking.pk, 1)
        layer = get_channel_layer()

        async def scenario():
            communicator = self.connect(self.operator)
            await communicator.connect()
            await layer.group_send(group, {"type": "zone.occupancy", "message": message})
            received = await communicator.receive_json_from()
            await ParkingMembership.objects.filter(user=self.operator).adelete()
            await layer.group_send(group, {"type": "zone.occupancy", "message": message})
            closed = await communicator.receive_output()
            await communicator.disconnect()
            return received, closed["type"]

        self.assertEqual(async_to_sync(scenario)(), (message, "websocket.close"))

    def test_outsiders_are_closed_without_data(self):
        outsider = User.objects.create_user(username="outsider")

        async def scenario():
            communicator = self.connect(outsider)
            await communicator.connect()
            output = await communicator.receive_output()
            await communicator.disconnect()
            return output["type"]

        self.assertEqual(async_to_sync(scenario)(), "websocket.close")
