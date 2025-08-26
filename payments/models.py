from django.utils import timezone
from django.db import models
from passenger.models import User
from booking.models import Booking

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    payment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    payment_mode = models.CharField(max_length=50, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'  # Set a default status, e.g., 'pending'
    )


    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status == "completed" and self.paid_at is None:
            self.paid_at = timezone.now()
        super().save(*args, **kwargs)