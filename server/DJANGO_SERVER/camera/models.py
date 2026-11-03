from django.db import models
import uuid


class Camera(models.Model):
    CAPTURE_CHOICES = (('snapshot', 'Snapshot'), ('rtsp', 'RTSP'), ('file', 'File'))

    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True , primary_key=True)
    parking = models.ForeignKey('parking.Parking', on_delete=models.CASCADE, null=True, blank=True, related_name='cameras')
    area  = models.IntegerField()
    path = models.CharField(max_length=200)
    ref = models.CharField(max_length=200)
    capture_mode = models.CharField(max_length=10, choices=CAPTURE_CHOICES, default='file')
    stream_url = models.CharField(max_length=300, blank=True)
