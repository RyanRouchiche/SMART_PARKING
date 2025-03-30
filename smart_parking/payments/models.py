from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()  # Dynamically get the user model

class Payments(models.Model):
    SUBSCRIPTION_CHOICE = (
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    subscription_type = models.CharField(max_length=10, choices=SUBSCRIPTION_CHOICE, blank=True, null=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.status}"

    def make_payment(self, amount, subscription_type=None):
        """
        Handles the payment process.
        """
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        
        self.amount = amount
        self.subscription_type = subscription_type
        self.status = 'completed'  # Simulate successful payment
        self.save()

    def update_status(self, new_status):
        """
        Updates the payment status.
        """
        if new_status not in dict(self.PAYMENT_STATUS_CHOICES):
            raise ValueError(f"Invalid status: {new_status}")
        
        self.status = new_status
        self.save()