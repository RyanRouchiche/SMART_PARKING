import cv2
import threading
import time

class ThreadedCameraManager:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.running = True
        self.latest_frame = None
        self.lock = threading.Lock()

        # Start a thread to continuously read frames
        self.thread = threading.Thread(target=self._update_frames, daemon=True)
        self.thread.start()

        # Get the FPS of the video
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def _update_frames(self):
        while self.running:
            if not self.cap.isOpened():
                print(f"Error: Video source is not open. Trying to reopen...")
                self.cap = cv2.VideoCapture(self.video_path)
                if not self.cap.isOpened():
                    print(f"Failed to reopen video source.")
                    time.sleep(1)  # Wait before retrying
                    continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("End of video reached or bad frame. Resetting...")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  
                time.sleep(0.1)  
                continue

            # Update the latest frame with a thread-safe lock
            with self.lock:
                self.latest_frame = frame

    def get_frame(self):
        with self.lock:
            return self.latest_frame

    def get_fps(self):
        return self.fps

    def stop(self):
        self.running = False
        self.thread.join()
        self.cap.release()
