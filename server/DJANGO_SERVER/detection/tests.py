import os
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest import mock

import cv2
import numpy as np
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.core import mail
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings

from camera.models import Camera
from .consumers import VideoFeedConsumer
from parking.models import Parking, ParkingMembership, Zone
from django.core.cache import cache

from users.models import User
from rest_framework.test import APITestCase

from . import events, health, history, state, stats
from .models import AvailabilitySnapshot
from shared.geometry import crop_size, order_corners
from shared.hours import is_open
from shared.naming import natural_key
from .worker import Supervisor, ZoneConfig, ZoneWorker, detect, load_zones, spot_transforms

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
        Zone.objects.create(parking=parking, number=1, spots={"P10": SQUARE, "P2": SQUARE, "P1": SQUARE})
        Zone.objects.create(parking=parking, number=2, spots={"P1": SQUARE})
        Zone.objects.create(parking=parking, number=3, spots={})
        Camera.objects.create(parking=parking, area=1, path="cam-1.mp4", ref="C1")
        Camera.objects.create(parking=parking, area=3, path="cam-3.mp4", ref="C3")

        configs = load_zones()

        self.assertEqual([(c.area, c.path, [n for n, _ in c.spots]) for c in configs], [(1, "cam-1.mp4", ["P1", "P2", "P10"])])

    def test_closed_parkings_are_not_watched(self):
        hours = {"mon": [["08:00", "18:00"]]}
        open_lot = Parking.objects.create(name="Open", opening_hours=hours)
        always_lot = Parking.objects.create(name="Always", opening_hours={})
        for parking in (open_lot, always_lot):
            Zone.objects.create(parking=parking, number=1, spots={"P1": SQUARE})
            Camera.objects.create(parking=parking, area=1, path=f"{parking.name}.mp4", ref="C")
        monday_noon = datetime(2026, 11, 2, 11, 0, tzinfo=dt_timezone.utc)
        monday_night = datetime(2026, 11, 2, 21, 0, tzinfo=dt_timezone.utc)

        self.assertEqual({c.path for c in load_zones(now=monday_noon)}, {"Open.mp4", "Always.mp4"})
        self.assertEqual({c.path for c in load_zones(now=monday_night)}, {"Always.mp4"})

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

    def test_deactivating_the_user_closes_the_stream(self):
        async def scenario():
            communicator = self.connect(self.operator)
            await communicator.connect()
            self.operator.is_active = False
            await self.operator.asave()
            output = await communicator.receive_output()
            await communicator.disconnect()
            return output["type"]

        self.assertEqual(async_to_sync(scenario)(), "websocket.close")

    def test_periodic_recheck_closes_when_signals_were_bypassed(self):
        message = {"area": 1, "available_spots": 0, "spot_details": []}
        group = events.zone_group(self.parking.pk, 1)
        layer = get_channel_layer()

        async def scenario():
            communicator = self.connect(self.operator)
            await communicator.connect()
            await User.objects.filter(pk=self.operator.pk).aupdate(is_active=False)
            with mock.patch("detection.consumers.RECHECK_INTERVAL", 0):
                await layer.group_send(group, {"type": "zone.occupancy", "message": message})
                output = await communicator.receive_output()
            await communicator.disconnect()
            return output["type"]

        self.assertEqual(async_to_sync(scenario)(), "websocket.close")

    def test_outsiders_are_closed_without_data(self):
        outsider = User.objects.create_user(username="outsider")

        async def scenario():
            communicator = self.connect(outsider)
            await communicator.connect()
            output = await communicator.receive_output()
            await communicator.disconnect()
            return output["type"]

        self.assertEqual(async_to_sync(scenario)(), "websocket.close")

    def test_the_latest_fresh_state_is_sent_on_connect(self):
        message = {"area": 1, "available_spots": 1, "spot_details": [{"spot": "P1", "status": "empty"}]}
        state.store(self.parking.pk, 1, message)

        async def scenario():
            communicator = self.connect(self.operator)
            await communicator.connect()
            received = await communicator.receive_json_from()
            await communicator.disconnect()
            return received

        self.assertEqual(async_to_sync(scenario)(), message)
        cache.clear()

    def test_a_stale_state_is_not_sent_on_connect(self):
        message = {"area": 1, "available_spots": 1, "spot_details": [{"spot": "P1", "status": "empty"}]}
        state.store(self.parking.pk, 1, message, now=0)

        async def scenario():
            communicator = self.connect(self.operator)
            await communicator.connect()
            nothing = await communicator.receive_nothing(0.3)
            await communicator.disconnect()
            return nothing

        self.assertTrue(async_to_sync(scenario)())
        cache.clear()


class OpeningHoursTests(SimpleTestCase):
    HOURS = {"mon": [["08:00", "12:00"], ["14:00", "18:00"]], "fri": [["22:00", "02:00"]]}

    def at(self, day, hour, minute=0):
        return datetime(2026, 11, 2 + day, hour, minute)

    def test_no_hours_means_always_open(self):
        self.assertTrue(is_open({}, self.at(0, 3)))

    def test_ranges_and_lunch_break(self):
        self.assertTrue(is_open(self.HOURS, self.at(0, 8)))
        self.assertFalse(is_open(self.HOURS, self.at(0, 12)))
        self.assertTrue(is_open(self.HOURS, self.at(0, 17, 59)))
        self.assertFalse(is_open(self.HOURS, self.at(1, 10)))

    def test_overnight_range_spills_into_the_next_day(self):
        self.assertTrue(is_open(self.HOURS, self.at(4, 23)))
        self.assertTrue(is_open(self.HOURS, self.at(5, 1, 30)))
        self.assertFalse(is_open(self.HOURS, self.at(5, 2)))
        self.assertFalse(is_open(self.HOURS, self.at(4, 1)))


class SpotOrderTests(TestCase):
    def test_natural_order_puts_p2_before_p10(self):
        self.assertEqual(sorted(["P10", "P2", "p1"], key=natural_key), ["p1", "P2", "P10"])

    def test_natural_order_never_fails_on_unicode_digits(self):
        names = ["P1²", "²", "P٣", "P10", "P2"]
        self.assertEqual(sorted(names, key=natural_key), ["P1²", "P2", "P٣", "P10", "²"])

    def test_layouts_come_back_in_natural_order_from_jsonb(self):
        parking = Parking.objects.create(name="A")
        Zone.objects.create(parking=parking, number=1, spots={"Spot 10": SQUARE, "Spot 9": SQUARE, "Spot 1": SQUARE})
        zone = Zone.objects.get(parking=parking, number=1)
        self.assertEqual(list(zone.ordered_spots), ["Spot 1", "Spot 9", "Spot 10"])


class StateTests(SimpleTestCase):
    MESSAGE = {"area": 2, "available_spots": 1, "spot_details": [{"spot": "P1", "status": "empty"}, {"spot": "P2", "status": "occupied"}]}

    def tearDown(self):
        cache.clear()

    def test_store_keeps_the_message_with_a_timestamp(self):
        state.store("lot", 2, self.MESSAGE, now=100)
        saved = state.latest("lot", 2)
        self.assertEqual((saved["total"], saved["errors"], saved["ts"]), (2, 0, 100))
        self.assertEqual(state.public_message(saved), self.MESSAGE)

    def test_state_turns_stale_after_fifteen_seconds(self):
        saved = state.build(self.MESSAGE, now=100)
        self.assertFalse(state.is_stale(saved, now=115))
        self.assertTrue(state.is_stale(saved, now=116))
        self.assertTrue(state.is_stale(None))

    def test_a_zone_where_every_spot_failed_is_stale(self):
        failed = {"area": 2, "available_spots": 0, "spot_details": [{"spot": "P1", "status": "error"}]}
        self.assertTrue(state.is_stale(state.build(failed, now=100), now=100))

    def test_parking_availability_sums_fresh_zones_only(self):
        state.store("lot", 1, self.MESSAGE, now=100)
        state.store("lot", 2, {"area": 2, "available_spots": 3, "spot_details": [{"spot": "P1", "status": "empty"}] * 3}, now=50)
        result = state.parking_availability("lot", [1, 2, 3], now=110)
        self.assertEqual((result["free"], result["total"], result["stale"]), (1, 2, False))
        self.assertEqual([z["stale"] for z in result["zones"]], [False, True, True])
        self.assertTrue(state.parking_availability("empty-lot", [1], now=110)["stale"])


class HistoryTests(TestCase):
    NOW = datetime(2026, 11, 3, 10, 0, tzinfo=dt_timezone.utc)

    def test_only_fresh_states_are_recorded(self):
        fresh = state.build({"area": 1, "available_spots": 4, "spot_details": [{"spot": "P", "status": "empty"}] * 6}, now=self.NOW.timestamp())
        old = state.build({"area": 2, "available_spots": 1, "spot_details": [{"spot": "P", "status": "empty"}]}, now=self.NOW.timestamp() - 60)
        parking_id = "11111111-1111-1111-1111-111111111111"

        self.assertEqual(history.record({(parking_id, 1): fresh, (parking_id, 2): old}, self.NOW), 1)
        row = AvailabilitySnapshot.objects.get()
        self.assertEqual((str(row.parking_id), row.area, row.free, row.total), (parking_id, 1, 4, 6))

    def test_purge_keeps_ninety_days(self):
        for days in (89, 91):
            AvailabilitySnapshot.objects.create(parking_id="11111111-1111-1111-1111-111111111111", area=1, taken_at=self.NOW - timedelta(days=days), free=1, total=2)
        self.assertEqual(history.purge(self.NOW), 1)
        self.assertEqual(AvailabilitySnapshot.objects.count(), 1)

    def test_supervisor_records_once_a_minute(self):
        class Publish:
            states = {}

            def __call__(self, *args):
                pass

            def snapshot(self):
                return self.states

        supervisor = Supervisor(publish=Publish())
        with mock.patch.object(history, "record") as record, mock.patch.object(history, "purge") as purge:
            supervisor.maintain(self.NOW)
            supervisor.maintain(self.NOW + timedelta(seconds=30))
            supervisor.maintain(self.NOW + timedelta(seconds=60))
        self.assertEqual(record.call_count, 2)
        self.assertEqual(purge.call_count, 1)


class SupervisionTests(TestCase):
    SPOTS = {"Spot 1": [[0, 0], [10, 0], [10, 10], [0, 10]], "Spot 2": [[0, 0], [10, 0], [10, 10], [0, 10]]}

    def setUp(self):
        cache.clear()
        self.visible = self.parking("Visible", published=True)
        self.draft = self.parking("Draft", published=False)
        self.closed = self.parking("Closed", published=True, hours={day: [] for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")})
        up = mock.patch("detection.health.model_server_up", return_value=True)
        up.start()
        self.addCleanup(up.stop)

    def tearDown(self):
        cache.clear()

    def parking(self, name, published, hours=None):
        from parking.models import Subscription
        parking = Parking.objects.create(name=name, latitude=36.7, longitude=3.0, is_published=published, opening_hours=hours or {})
        Subscription.objects.filter(parking=parking).update(status=Subscription.ACTIVE)
        Zone.objects.create(parking=parking, number=1, spots=self.SPOTS)
        return parking

    def publish(self, parking, statuses, age=0):
        details = [{"spot": f"Spot {i}", "status": s} for i, s in enumerate(statuses, 1)]
        state.store(parking.pk, 1, {"area": 1, "available_spots": statuses.count("empty"), "spot_details": details}, now=time.time() - age)

    def problems(self):
        return [p for p in health.report()["problems"] if "Visible" in p or "Draft" in p or "Closed" in p or "modèle" in p]

    def test_only_open_visible_parkings_without_recent_data_are_problems(self):
        self.assertEqual(self.problems(), ["Visible, zone 1 : aucune donnée"])
        self.publish(self.visible, ["empty", "occupied"])
        self.assertEqual(self.problems(), [])

    def test_a_short_gap_is_tolerated_but_a_dead_camera_is_not(self):
        self.publish(self.visible, ["empty", "occupied"], age=60)
        self.assertEqual(self.problems(), [])
        self.publish(self.visible, ["error", "error"])
        self.assertEqual(self.problems(), ["Visible, zone 1 : dernière donnée il y a 0 s"])

    def test_model_server_outage_is_reported(self):
        self.publish(self.visible, ["empty", "occupied"])
        with mock.patch("detection.health.model_server_up", return_value=False):
            self.assertEqual(self.problems(), ["Serveur du modèle injoignable"])

    @override_settings(TEAM_EMAIL="team@example.com")
    def test_alerts_are_sent_only_when_problems_change(self):
        self.assertTrue(health.alert(["A"]))
        self.assertFalse(health.alert(["A"]))
        self.assertTrue(health.alert([]))
        self.assertEqual([m.subject for m in mail.outbox], ["Supervision : 1 problème(s)", "Supervision : tout est rétabli"])

    def test_the_page_is_for_staff_only(self):
        url = "/admin/supervision/"
        User.objects.create_user(username="owner", password="x", user_type="admin")
        self.client.login(username="owner", password="x")
        self.assertEqual(self.client.get(url).status_code, 302)
        User.objects.create_user(username="staff", password="x", is_staff=True)
        self.client.login(username="staff", password="x")
        response = self.client.get(url)
        self.assertContains(response, "Visible")
        self.assertContains(response, "aucune donnée")


class StatsTests(APITestCase):
    URL = "/api/parking/stats/"

    def setUp(self):
        self.parking = Parking.objects.create(name="Mine")
        self.other = Parking.objects.create(name="Other")
        self.owner = User.objects.create_user(username="boss", password="x", user_type="admin")
        self.operator = User.objects.create_user(username="op", password="x")
        ParkingMembership.objects.create(user=self.owner, parking=self.parking, role="owner")
        ParkingMembership.objects.create(user=self.operator, parking=self.parking, role="operator")

    def snap(self, parking, when, area, free, total):
        AvailabilitySnapshot.objects.create(parking_id=parking.pk, area=area, taken_at=when, free=free, total=total)

    def test_occupancy_is_aggregated_per_local_hour_over_zones(self):
        nine = datetime(2026, 11, 2, 8, 0, tzinfo=dt_timezone.utc)
        self.snap(self.parking, nine, 1, free=1, total=4)
        self.snap(self.parking, nine, 2, free=3, total=4)
        self.snap(self.parking, nine + timedelta(minutes=30), 1, free=0, total=4)
        self.snap(self.parking, nine + timedelta(hours=1), 1, free=4, total=4)
        self.snap(self.other, nine, 1, free=0, total=4)
        self.snap(self.parking, nine - timedelta(days=91), 1, free=0, total=4)

        rows = stats.hourly_occupancy(self.parking.pk, 90, now=nine + timedelta(hours=2))

        self.assertEqual(rows, [["2026-11-02", 9, round(100 * (1 - 4 / 12), 1)], ["2026-11-02", 10, 0.0]])

    def test_only_owners_see_their_statistics(self):
        self.client.force_authenticate(self.operator)
        self.assertEqual(self.client.get(self.URL).status_code, 403)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(self.URL, {"parking": str(self.other.pk)}).status_code, 403)
        response = self.client.get(self.URL, {"days": "500"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["days"], 90)
        self.assertEqual(self.client.get(self.URL, {"days": "x"}).status_code, 400)
