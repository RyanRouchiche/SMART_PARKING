from datetime import timedelta

from . import state
from .models import AvailabilitySnapshot

RECORD_INTERVAL = 60
PURGE_INTERVAL = 24 * 3600
RETENTION_DAYS = 90


def record(states, now):
    rows = [
        AvailabilitySnapshot(parking_id=parking_id, area=area, taken_at=now, free=s['available_spots'], total=s['total'])
        for (parking_id, area), s in states.items()
        if not state.is_stale(s, now.timestamp())
    ]
    AvailabilitySnapshot.objects.bulk_create(rows)
    return len(rows)


def purge(now):
    deleted, _ = AvailabilitySnapshot.objects.filter(taken_at__lt=now - timedelta(days=RETENTION_DAYS)).delete()
    return deleted
