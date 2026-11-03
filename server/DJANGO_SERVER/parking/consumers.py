import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs

import cv2
import numpy as np
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.exceptions import PermissionDenied

from camera.models import Camera
from camera.sources import open_source
from .access import resolve_parking
from .models import ParkingMembership
from .model_client import predict_spots

logger = logging.getLogger(__name__)

SPOT_SIZE = 180
SPOT_DST = np.float32([[0, 0], [SPOT_SIZE, 0], [SPOT_SIZE, SPOT_SIZE], [0, SPOT_SIZE]])
CAPTURE_TIMEOUTS = [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000]


def zone_for(user, area, parking_id):
    try:
        parking = resolve_parking(user, parking_id)
    except PermissionDenied:
        return None, None, None
    zone = parking.zones.filter(number=area).first()
    path = Camera.objects.filter(parking=parking, area=area).values_list('path', flat=True).first()
    return (zone.spots if zone else None), path, parking.pk


def still_member(user_id, parking_id):
    return ParkingMembership.objects.filter(user_id=user_id, parking_id=parking_id, user__is_active=True).exists()


def open_capture(path):
    return open_source(path, CAPTURE_TIMEOUTS)


load_zone = database_sync_to_async(zone_for)
check_member = database_sync_to_async(still_member)


class VideoFeedConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.area = int(self.scope['url_route']['kwargs']['area'])
        self.streaming = False
        self.cap = None
        self.tasks = []
        self.executor = ThreadPoolExecutor(max_workers=1)
        parking_id = parse_qs(self.scope.get('query_string', b'').decode()).get('parking', [None])[0]
        self.area_coordinates, video_path, self.parking_pk = await load_zone(self.scope['user'], self.area, parking_id)
        await self.accept()

        if not self.area_coordinates:
            logger.warning(f"No coordinates found for area {self.area}")
            return await self.close()

        self.cap = await self.run(open_capture, video_path) if video_path else None
        if self.cap is None or not self.cap.isOpened():
            logger.warning(f"Unable to open video for area {self.area}")
            return await self.close()

        self.streaming = True
        self.tasks = [
            asyncio.create_task(self.video_loop()),
            asyncio.create_task(self.prediction_loop()),
        ]

    def run(self, fn, *args):
        return asyncio.get_running_loop().run_in_executor(self.executor, fn, *args)

    async def disconnect(self, close_code):
        self.streaming = False
        for task in self.tasks:
            task.cancel()
        if self.cap is not None:
            await self.run(self.cap.release)
        self.executor.shutdown(wait=False)

    async def video_loop(self):
        frame_delay = 1 / (self.cap.get(cv2.CAP_PROP_FPS) or 30)
        while self.streaming:
            start_time = time.time()
            if not await self.run(self.cap.grab):
                await self.run(self.cap.set, cv2.CAP_PROP_POS_FRAMES, 0)
            await asyncio.sleep(max(0, frame_delay - (time.time() - start_time)))

    async def prediction_loop(self):
        loop = asyncio.get_running_loop()
        names = list(self.area_coordinates)
        transforms = [cv2.getPerspectiveTransform(np.float32(self.area_coordinates[n]), SPOT_DST) for n in names]
        while self.streaming:
            ret, frame = await self.run(self.cap.retrieve)
            if not ret:
                await asyncio.sleep(0.1)
                continue

            crops = await self.run(lambda: [cv2.warpPerspective(frame, m, (SPOT_SIZE, SPOT_SIZE)) for m in transforms])
            try:
                statuses = await loop.run_in_executor(None, predict_spots, crops)
            except Exception as e:
                logger.error(f"Prediction error in area {self.area}: {e}")
                statuses = ['error'] * len(names)

            if not await check_member(self.scope['user'].pk, self.parking_pk):
                self.streaming = False
                return await self.close()
            await self.send(text_data=json.dumps({
                'area': self.area,
                'available_spots': statuses.count('empty'),
                'spot_details': [{'spot': n, 'status': s} for n, s in zip(names, statuses)],
            }))
            await asyncio.sleep(5)
