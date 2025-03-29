import cv2
class Camera:
    def __init__(self, video_path, floor=None):
        self.video_path = video_path
        self.floor = floor
        self.cap = cv2.VideoCapture(video_path)  # Initialize the video capture object

        if not self.cap.isOpened():
            print(f"Error: Unable to open video source for floor {floor}")

    def getFrame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                print(f"End of video reached for floor {self.floor}. Restarting...")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to the first frame
                return None
        else:
            print(f"Error: Video source is not open for floor {self.floor}")
            return None

    def reset(self):
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to the first frame
            
    def restart(self):
        self.cap.release()
        self.cap = cv2.VideoCapture(self.video_path)
