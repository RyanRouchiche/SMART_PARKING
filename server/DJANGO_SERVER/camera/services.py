import base64
import logging
from contextlib import contextmanager

import cv2

from detection.capture import VideoSource
from .models import Camera

logger = logging.getLogger(__name__)


@contextmanager
def parking_sources(parking_id):
    sources = {area: VideoSource(path) for area, path in Camera.objects.filter(parking_id=parking_id).values_list('area', 'path')}
    try:
        yield {area: source for area, source in sources.items() if source.is_open}
    finally:
        for source in sources.values():
            source.release()


def current_frames(parking_id, areas=None):
    with parking_sources(parking_id) as sources:
        frames = {}
        for area, source in sources.items():
            if areas is not None and area not in areas:
                continue
            frame = source.read()
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
