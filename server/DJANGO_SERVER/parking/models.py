import uuid

from django.conf import settings
from django.db import models

from shared.naming import natural_key


class Parking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    opening_hours = models.JSONField(default=dict, blank=True)
    pricing_text = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ParkingMembership(models.Model):
    OWNER = 'owner'
    OPERATOR = 'operator'
    ROLE_CHOICES = ((OWNER, 'Owner'), (OPERATOR, 'Operator'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    parking = models.ForeignKey(Parking, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'parking'], name='unique_membership')]

    def __str__(self):
        return f"{self.user} · {self.parking} · {self.role}"


class Zone(models.Model):
    parking = models.ForeignKey(Parking, on_delete=models.CASCADE, related_name='zones')
    camera = models.OneToOneField('camera.Camera', on_delete=models.SET_NULL, null=True, blank=True, related_name='zone')
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=60, blank=True)
    spots = models.JSONField(default=dict, blank=True)
    reference_size = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['number']
        constraints = [models.UniqueConstraint(fields=['parking', 'number'], name='unique_zone_number')]

    def __str__(self):
        return f"{self.parking} · Z{self.number}"

    @property
    def ordered_spots(self):
        return dict(sorted(self.spots.items(), key=lambda item: natural_key(item[0])))
