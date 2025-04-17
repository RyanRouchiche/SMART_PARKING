from django.db import models
from django.contrib.auth.models import AbstractUser
from django.apps import apps
import uuid
from django.utils import timezone


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('guest', 'Guest'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='guest')
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')

    def __str__(self):
        return self.username
    
class auth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='auth')
    refresh_token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"Auth token for {self.user.username}"
    
    def is_valid(self):

        return not self.is_revoked and self.expires_at > timezone.now()