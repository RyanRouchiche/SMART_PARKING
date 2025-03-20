import cv2

class Camera:
    def __init__(self, resource, floor):
        self.capture = cv2.VideoCapture(resource)
        self.floor = floor  

    def getFrame(self):
        ret, frame = self.capture.read()
        if not ret:
            print(f"Error: Unable to capture a frame from the camera on floor {self.floor}")
            return None
        return frame


