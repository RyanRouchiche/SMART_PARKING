import asyncio
import logging
import threading

from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


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
        threading.Thread(target=self.loop.run_forever, daemon=True, name="publisher").start()

    def __call__(self, parking_id, area, message):
        future = asyncio.run_coroutine_threadsafe(
            self.layer.group_send(zone_group(parking_id, area), {'type': 'zone.occupancy', 'message': message}),
            self.loop,
        )
        future.add_done_callback(self.report)

    @staticmethod
    def report(future):
        if future.exception():
            logger.error(f"Publish failed: {future.exception()}")
