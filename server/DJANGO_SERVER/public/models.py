from django.db import models


class OwnerRequest(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('visit_planned', 'Visit planned'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    FIBER_CHOICES = (('yes', 'Yes'), ('no', 'No'), ('unknown', 'Unknown'))
    LANGUAGE_CHOICES = (('fr', 'Français'), ('ar', 'العربية'))

    name = models.CharField(max_length=120)
    company = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32)
    email = models.EmailField()
    parking_name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()
    cameras = models.PositiveIntegerField()
    fiber = models.CharField(max_length=10, choices=FIBER_CHOICES, default='unknown')
    message = models.TextField(blank=True, max_length=2000)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='fr')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    parking = models.ForeignKey('parking.Parking', on_delete=models.SET_NULL, null=True, blank=True, related_name='owner_requests')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.parking_name} · {self.name}"
