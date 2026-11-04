import logging
import threading
import time
import zlib
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from camera.interface import VideoSource, all_camera_paths
from parking.interface import all_zone_layouts
from shared.geometry import normalized_crops, spot_transforms
from shared.hours import is_open
from . import events, history
from .classifier import classify

logger = logging.getLogger(__name__)

PREDICTION_INTERVAL = 5
RETRY_DELAY = 10
MAX_FAILED_GRABS = 50


@dataclass(frozen=True)
class ZoneConfig:
    parking_id: str
    area: int
    path: str
    spots: tuple

    @property
    def key(self):
        return self.parking_id, self.area


def detect(frame, area, transforms, classifier=classify):
    names = list(transforms)
    try:
        statuses = classifier(normalized_crops(frame, transforms))
    except Exception as e:
        logger.error(f"Prediction error in area {area}: {e}")
        statuses = ['error'] * len(names)
    return events.occupancy_message(area, names, statuses)


class ZoneWorker(threading.Thread):
    def __init__(self, config, publish, classifier=classify):
        super().__init__(daemon=True, name=f"zone-{config.parking_id}-{config.area}")
        self.config = config
        self.publish = publish
        self.classifier = classifier
        self.stopped = threading.Event()

    def stop(self):
        self.stopped.set()

    def run(self):
        while not self.stopped.is_set():
            source = VideoSource(self.config.path)
            if source.is_open:
                self.stream(source)
            else:
                logger.warning(f"Unable to open video for area {self.config.area}")
            source.release()
            self.stopped.wait(RETRY_DELAY)

    def stream(self, source):
        transforms = spot_transforms(dict(self.config.spots))
        delay = source.frame_delay
        next_prediction = 0
        failures = 0
        while not self.stopped.is_set() and failures < MAX_FAILED_GRABS:
            started = time.monotonic()
            failures = 0 if source.grab() else failures + 1
            if started >= next_prediction:
                frame = source.latest_frame()
                if frame is not None:
                    message = detect(frame, self.config.area, transforms, self.classifier)
                    self.publish(self.config.parking_id, self.config.area, message)
                    next_prediction = time.monotonic() + PREDICTION_INTERVAL
            self.stopped.wait(max(0, delay - (time.monotonic() - started)))


def in_shard(config, shard, shards):
    return zlib.crc32(f"{config.parking_id}:{config.area}".encode()) % shards == shard


def parking_time(now=None):
    return (now or timezone.now()).astimezone(ZoneInfo(settings.PARKING_TIME_ZONE))


def parking_areas():
    areas = {}
    for parking_id, number, _, _ in all_zone_layouts():
        areas.setdefault(str(parking_id), []).append(number)
    return areas


def load_zones(shard=0, shards=1, now=None):
    paths = {(str(p), a): path for (p, a), path in all_camera_paths().items()}
    moment = parking_time(now)
    configs = []
    for parking_id, number, spots, hours in all_zone_layouts():
        path = paths.get((str(parking_id), number))
        if path and is_open(hours, moment):
            config = ZoneConfig(str(parking_id), number, path, tuple((n, tuple(map(tuple, p))) for n, p in spots.items()))
            if in_shard(config, shard, shards):
                configs.append(config)
    return configs


class Supervisor:
    def __init__(self, shard=0, shards=1, worker_class=ZoneWorker, publish=None):
        self.shard = shard
        self.shards = shards
        self.worker_class = worker_class
        self.publish = publish or events.Publisher()
        self.workers = {}
        self.recorded_at = None
        self.purged_at = None

    def maintain(self, now=None):
        now = now or timezone.now()
        if self.recorded_at is None or (now - self.recorded_at).total_seconds() >= history.RECORD_INTERVAL:
            history.record(self.publish.snapshot(), now)
            self.recorded_at = now
        if self.purged_at is None or (now - self.purged_at).total_seconds() >= history.PURGE_INTERVAL:
            history.purge(now)
            self.purged_at = now

    def sync(self):
        close_old_connections()
        if hasattr(self.publish, 'areas'):
            self.publish.areas = parking_areas()
        wanted = {c.key: c for c in load_zones(self.shard, self.shards)}
        for key, worker in list(self.workers.items()):
            if wanted.get(key) != worker.config:
                worker.stop()
                del self.workers[key]
        for key, config in wanted.items():
            if key not in self.workers:
                self.workers[key] = self.worker_class(config, self.publish)
                self.workers[key].start()

    def stop(self):
        for worker in self.workers.values():
            worker.stop()
        self.workers.clear()
