from django.db import models


class AvailabilitySnapshot(models.Model):
    parking_id = models.UUIDField()
    area = models.PositiveIntegerField()
    taken_at = models.DateTimeField(db_index=True)
    free = models.PositiveSmallIntegerField()
    total = models.PositiveSmallIntegerField()

    class Meta:
        indexes = [models.Index(fields=['parking_id', 'taken_at'], name='snapshot_parking_time')]
