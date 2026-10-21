import cv2
from .models import Camera as CamModel
from channels.db import database_sync_to_async


class Camera:
    def __init__(self, video_path, area=None):
        self.video_path = video_path
        self.area = area
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print(f"Error: Unable to open video source for area {area}")

    def getFrame(self):
        if not self.cap.isOpened():
            print(f"Error: Video source is not open for area {self.area}")
            return None
        ret, frame = self.cap.read()
        if ret:
            return frame
        print(f"End of video reached for area {self.area}. Restarting...")
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        return None

    def reset(self):
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    @staticmethod
    @database_sync_to_async
    def get_available_cameras():
        return dict(CamModel.objects.values_list('area', 'path'))
