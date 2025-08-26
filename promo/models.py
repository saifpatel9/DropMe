# promo/models.py

from django.db import models
from django.utils.timezone import now 

class PromoCode(models.Model):
    PROMO_TYPE_CHOICES = [
        ('Flat', 'Flat'),
        ('Percent', 'Percent'),
    ]

    promo_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentage_value = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True,
                                           help_text="Percentage discount for percentage-based promo codes")
    start_time = models.DateTimeField(null=True, blank=True)
    expiry_time = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    max_usage = models.IntegerField(null=True, blank=True)
    max_usage_per_user = models.IntegerField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=PROMO_TYPE_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.code

    @property
    def is_active(self):
        # This property remains, but we'll use status_display in the template
        current_time = now()
        return self.start_time <= current_time <= self.expiry_time
    
    @property
    def status_display(self):
        current_time = now()
        if self.start_time and self.expiry_time:
            if current_time < self.start_time:
                return "Upcoming"
            elif self.start_time <= current_time <= self.expiry_time:
                return "Active"
            else: # current_time > self.expiry_time
                return "Expired"
        return "Unknown" # Fallback for cases where times might be null