from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncHour
from django.utils import timezone

from .models import AvailabilitySnapshot

MAX_DAYS = 90


def hourly_occupancy(parking_id, days, now=None):
    since = (now or timezone.now()) - timedelta(days=days)
    rows = (
        AvailabilitySnapshot.objects.filter(parking_id=parking_id, taken_at__gte=since)
        .annotate(hour=TruncHour('taken_at', tzinfo=ZoneInfo(settings.PARKING_TIME_ZONE)))
        .values('hour')
        .annotate(free=Sum('free'), total=Sum('total'))
        .order_by('hour')
    )
    return [
        [row['hour'].date().isoformat(), row['hour'].hour, round(100 * (1 - row['free'] / row['total']), 1)]
        for row in rows
        if row['total']
    ]
