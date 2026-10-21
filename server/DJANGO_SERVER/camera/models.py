from django.db import models
import uuid

# Create your models here.

class Camera(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True , primary_key=True)
    area  = models.IntegerField()
    path = models.CharField(max_length=200)
    ref = models.CharField(max_length=200)
    
    