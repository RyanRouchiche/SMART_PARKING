import cv2

from camera.sources import is_url, open_source

CAPTURE_TIMEOUTS = [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000]


class VideoSource:
    def __init__(self, path, timeouts=True):
        self.path = path
        self.cap = open_source(path, CAPTURE_TIMEOUTS) if timeouts else open_source(path)
        if is_url(path):
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    @property
    def is_open(self):
        return self.cap.isOpened()

    @property
    def frame_delay(self):
        return 1 / (self.cap.get(cv2.CAP_PROP_FPS) or 30)

    def grab(self):
        if self.cap.grab():
            return True
        self.rewind()
        return False

    def latest_frame(self):
        ok, frame = self.cap.retrieve()
        return frame if ok else None

    def read(self):
        if not self.is_open:
            return None
        ok, frame = self.cap.read()
        if ok:
            return frame
        self.rewind()
        return None

    def rewind(self):
        if self.is_open:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def release(self):
        self.cap.release()
