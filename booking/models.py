from django.db import models
from django.utils import timezone
from driver.models import Driver
from passenger.models import User
from services.models import ServiceType
from django.utils import timezone

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Arrived', 'Arrived'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    booking_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)  # Changed from 'User' to User
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    pickup_location = models.CharField(max_length=255, blank=True, null=True)
    dropoff_location = models.CharField(max_length=255, blank=True, null=True)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    drop_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    drop_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    scheduled_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True)
    fare = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    duration_min = models.IntegerField(blank=True, null=True)
    service_type = models.ForeignKey(ServiceType, models.DO_NOTHING, blank=True, null=True)
    payment_mode = models.CharField(max_length=50, null=True, blank=True)
    is_immediate = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Booking #{self.booking_id} - {self.status}"
    


class RideRequest(models.Model):
    STATUS_CHOICES = [
        ('Requested', 'Requested'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Expired', 'Expired'),
    ]

    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pickup_location = models.CharField(max_length=255, blank=False, null=False)
    dropoff_location = models.CharField(max_length=255, blank=False, null=False)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=False, null=False)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=False, null=False)
    drop_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=False, null=False)
    drop_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=False, null=False)
    scheduled_time = models.DateTimeField(default=timezone.now)
    fare = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Requested')
    payment_mode = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        booking_info = f"Booking #{self.booking.booking_id}" if self.booking else "No Booking Yet"
        return f"RideRequest to Driver {self.driver_id} - {booking_info}"