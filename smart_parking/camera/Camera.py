import cv2
from .models import Camera as CamModel
from .serializers import CameraSerializer 
from channels.db import database_sync_to_async
class Camera:
    def __init__(self, video_path, area=None):
        self.video_path = video_path
        self.area = area
        self.cap = cv2.VideoCapture(video_path) 
        if not self.cap.isOpened():
            print(f"Error: Unable to open video source for area {area}")

    def getFrame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                print(f"End of video reached for area {self.area}. Restarting...")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) 
                return None
        else:
            print(f"Error: Video source is not open for area {self.area}")
            return None

    def reset(self):
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  
            
    def restart(self):
        self.cap.release()
        self.cap = cv2.VideoCapture(self.video_path)
    
    @staticmethod
    @database_sync_to_async
    def get_available_cameras():
        cams = CamModel.objects.all()
        serializer = CameraSerializer(cams, many=True)
        
        active_cameras = {}

        for camera_data in serializer.data:
            if camera_data['is_active']: 
                area = camera_data['area']
                path = camera_data['path']
                
                active_cameras[int(area)] = path
        
        return active_cameras
    
