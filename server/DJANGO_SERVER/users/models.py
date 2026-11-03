import hashlib

from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils import timezone


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('guest', 'Guest'),
        ('driver', 'Driver'),
    )
    LANGUAGE_CHOICES = (('fr', 'Français'), ('ar', 'العربية'))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='guest')
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    phone = models.CharField(max_length=32, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='fr')

    def __str__(self):
        return self.username
    
def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


class auth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='auth')
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"Auth token for {self.user.username}"
    
    def is_valid(self):

        return not self.is_revoked and self.expires_at > timezone.now()