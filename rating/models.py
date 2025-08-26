from django.db import models
from django.contrib.auth import get_user_model
from booking.models import Booking
from driver.models import Driver

User = get_user_model()

class Rating(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'), 
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    GIVEN_BY_CHOICES = [
        ('user', 'User'),
        ('driver', 'Driver'),
    ]

    rating_id = models.BigAutoField(primary_key=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='ratings')
    User = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings', null=True, blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='driver_ratings', null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comments = models.TextField(blank=True, null=True)
    given_by = models.CharField(max_length=10, choices=GIVEN_BY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        unique_together = ('booking', 'given_by')  # Prevents duplicate ratings for same booking by same entity
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rating} star rating for booking #{self.booking.booking_id} by {self.given_by}"


