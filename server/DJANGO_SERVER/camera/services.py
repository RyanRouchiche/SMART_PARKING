import base64
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import cv2
from django.core.cache import cache

from detection.capture import VideoSource
from .models import Camera

logger = logging.getLogger(__name__)

HEALTH_TTL = 30
PROBE_WORKERS = 8


def in_parallel(fn, items):
    items = list(items)
    if not items:
        return []
    with ThreadPoolExecutor(max_workers=min(PROBE_WORKERS, len(items))) as pool:
        return list(pool.map(fn, items))


def probe(path):
    source = VideoSource(path)
    try:
        return source.read() is not None
    finally:
        source.release()


def health_key(path):
    return f"camera-health:{hashlib.sha256(path.encode()).hexdigest()}"


def camera_health(paths):
    paths = set(paths)
    cached = cache.get_many([health_key(p) for p in paths])
    known = {p: cached[health_key(p)] for p in paths if health_key(p) in cached}
    missing = [p for p in paths if p not in known]
    fresh = dict(zip(missing, in_parallel(probe, missing)))
    cache.set_many({health_key(p): ok for p, ok in fresh.items()}, HEALTH_TTL)
    return {**known, **fresh}


@contextmanager
def parking_sources(parking_id):
    rows = list(Camera.objects.filter(parking_id=parking_id).values_list('area', 'path'))
    sources = dict(zip([area for area, _ in rows], in_parallel(VideoSource, [path for _, path in rows])))
    try:
        yield {area: source for area, source in sources.items() if source.is_open}
    finally:
        for source in sources.values():
            source.release()


def current_frames(parking_id, areas=None):
    with parking_sources(parking_id) as sources:
        wanted = [(area, source) for area, source in sources.items() if areas is None or area in areas]
        frames = {}
        for (area, _), frame in zip(wanted, in_parallel(lambda item: item[1].read(), wanted)):
            if frame is None:
                logger.warning(f"Unable to capture a frame in area {area}")
                continue
            frames[area] = frame
        return frames


def snapshots(parking_id):
    images = {}
    for area, frame in current_frames(parking_id).items():
        _, buffer = cv2.imencode('.jpg', frame)
        images[area] = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
    return images


def add_cameras(parking, rows):
    return Camera.objects.bulk_create([Camera(parking=parking, **row) for row in rows])


def delete_camera(camera_id, parkings):
    deleted, _ = Camera.objects.filter(id=camera_id, parking__in=parkings).delete()
    return bool(deleted)
