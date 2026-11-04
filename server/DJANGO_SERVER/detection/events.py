import asyncio
import logging
import threading
import time
from functools import lru_cache

import redis
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.cache import cache

from . import state

logger = logging.getLogger(__name__)

STREAM = 'events:availability'
STREAM_MAX = 10000


@lru_cache(maxsize=None)
def stream_client():
    return redis.Redis.from_url(settings.REDIS_URL)


def free_key(parking_id):
    return f"parking_free:{parking_id}"


def announce_if_freed(parking_id, areas, client=None):
    free = state.parking_availability(parking_id, areas)['free']
    before = cache.get(free_key(parking_id))
    cache.set(free_key(parking_id), free, state.STATE_TTL)
    if before != 0 or not free:
        return False
    (client or stream_client()).xadd(
        STREAM,
        {'parking_id': str(parking_id), 'free_before': 0, 'free_after': free, 'ts': time.time()},
        maxlen=STREAM_MAX,
        approximate=True,
    )
    return True


def zone_group(parking_id, area):
    return f"zone_{parking_id}_{area}"


def occupancy_message(area, names, statuses):
    return {
        'area': area,
        'available_spots': statuses.count('empty'),
        'spot_details': [{'spot': n, 'status': s} for n, s in zip(names, statuses)],
    }


class Publisher:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.layer = get_channel_layer()
        self.latest = {}
        self.areas = {}
        self.lock = threading.Lock()
        threading.Thread(target=self.loop.run_forever, daemon=True, name="publisher").start()

    def snapshot(self):
        with self.lock:
            return dict(self.latest)

    def __call__(self, parking_id, area, message):
        try:
            saved = state.store(parking_id, area, message)
            with self.lock:
                self.latest[(parking_id, area)] = saved
            announce_if_freed(parking_id, self.areas.get(parking_id, [area]))
        except Exception as e:
            logger.error(f"State store failed: {e}")
        future = asyncio.run_coroutine_threadsafe(
            self.layer.group_send(zone_group(parking_id, area), {'type': 'zone.occupancy', 'message': message}),
            self.loop,
        )
        future.add_done_callback(self.report)

    @staticmethod
    def report(future):
        if future.exception():
            logger.error(f"Publish failed: {future.exception()}")
