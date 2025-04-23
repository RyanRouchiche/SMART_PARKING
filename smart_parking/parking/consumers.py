import json
import cv2
import asyncio
import base64
import numpy as np
import os
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from tensorflow.keras.models import load_model
from .model.services import predict_single_image
import concurrent.futures

class VideoFeedConsumer(AsyncWebsocketConsumer):
    video_paths = {
        1: os.path.join(settings.BASE_DIR, 'parking', 'Data', 'parking_crop_loop.mp4'),
    }
    coordinates_file = os.path.join(settings.BASE_DIR, 'parking', 'Spots', 'coordinates.json')

    async def connect(self):
        self.floor = int(self.scope['url_route']['kwargs']['floor'])
        self.video_path = self.video_paths.get(self.floor)
        self.streaming = True
        self.predictions = {}
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.model = load_model(os.path.join(settings.BASE_DIR, 'parking', 'model', 'clean_car_classifier.keras'))
        await self.accept()
        print(f"[VideoFeedConsumer] Connected to WebSocket (floor {self.floor})")

        try:
            with open(self.coordinates_file, "r", encoding="utf-8") as f:
                coordinates_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading coordinates: {e}")
            return

        self.floor_coordinates = next(
            (f["coordinates"] for f in coordinates_data if f["floor"] == str(self.floor)),
            None
        )
        if not self.floor_coordinates:
            print(f"No coordinates found for floor {self.floor}")
            return

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            print(f"Error: Unable to open video file {self.video_path}")
            return

        asyncio.create_task(self.video_loop())
        asyncio.create_task(self.prediction_loop())

    async def disconnect(self, close_code):
        self.streaming = False
        print(f"[VideoFeedConsumer] Disconnected from WebSocket (floor {self.floor})")
        await super().disconnect(close_code)
        self.cap.release()

    async def video_loop(self):
        while self.streaming:
            start_time = time.time()
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                await asyncio.sleep(0.01)
                continue

            # Draw predictions on the frame
            for spot_name, spot_points in self.floor_coordinates.items():
                status = self.predictions.get(spot_name, 'empty')
                color = (0, 255, 0) if status == 'empty' else (0, 0, 255)
                self.draw_spot_overlay(frame, spot_points, color)

            await self.send_video_frame(frame)

            elapsed = time.time() - start_time
            await asyncio.sleep(max(0, 1 / 30 - elapsed))  

    async def prediction_loop(self):
        while self.streaming:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    continue

                tasks = []
                for spot_name, spot_points in self.floor_coordinates.items():
                    cropped = self.apply_perspective_transform(frame, spot_points)
                    task = asyncio.get_event_loop().run_in_executor(
                        self.executor, predict_single_image, self.model, cropped
                    )
                    tasks.append((spot_name, task))

                for spot_name, task in tasks:
                    try:
                        status = await task
                        self.predictions[spot_name] = status
                    except Exception as e:
                        print(f"Prediction error on {spot_name}: {e}")
                        self.predictions[spot_name] = 'error'

                print(f"[PredictionLoop] Predictions updated for floor {self.floor}")
                await asyncio.sleep(5)  
            except Exception as e:
                print(f"[PredictionLoop Error] {e}")
                await asyncio.sleep(10)

    def draw_spot_overlay(self, frame, points, color):
        pts = np.array(points, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)

    async def send_video_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        encoded = base64.b64encode(buffer).decode('utf-8')
        available_spots = sum(1 for status in self.predictions.values() if status == 'empty')

        await self.send(text_data=json.dumps({
            'floor': self.floor,
            'video_frame': encoded,
            'available_spots': available_spots
        }))

    def apply_perspective_transform(self, frame, spot_points):
        src = np.float32(spot_points)
        dst = np.float32([[0, 0], [180, 0], [180, 180], [0, 180]])
        matrix = cv2.getPerspectiveTransform(src, dst)
        return cv2.warpPerspective(frame, matrix, (180, 180))

