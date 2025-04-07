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

    def get_payments(self):
        """
        Retrieves all payments associated with the user.
        """
        Payments = apps.get_model('payments', 'Payments')  # Dynamically get the Payments model
        return Payments.objects.filter(user=self)

    def create_guest(self, username, password):
        """
        Allows an admin to create a guest user.
        """
        if not self.can_create_guest():
            raise ValueError("You cannot create a guest account.")
        
        if self.user_type != 'admin':
            raise ValueError("Only admin users can create a guest account.")
        
        # Ensure the username is unique
        if User.objects.filter(username=username).exists():
            raise ValueError("A user with this username already exists.")
        
        # Create the guest user
        guest_user = User.objects.create_user(
            username=username,
            password=password,
            user_type='guest',
            created_by=self
        )
        return guest_user

    def can_create_guest(self):
        """
        Checks if an admin can create a guest account based on their latest payment.
        """
        if self.user_type != 'admin':
            return False
        
        # Get the latest completed payment
        Payments = apps.get_model('payments', 'Payments')  # Dynamically get the Payments model
        latest_payment = self.get_payments().filter(status="completed").order_by("-created_at").first()
        if not latest_payment:
            return False
        
        # Determine the maximum number of guests allowed
        max_guests = 2 if latest_payment.subscription_type == 'standard' else 5
        guest_count = User.objects.filter(is_active=True, user_type='guest', created_by=self).count()
        return guest_count < max_guests

    def __str__(self):
        return self.username
    
class auth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='auth')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    exipred_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"Auth token for {self.user.username}"
    
    def is_valid(self):

        return not self.is_revoked and self.exipred_at > timezone.now()