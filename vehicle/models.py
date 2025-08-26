from django.db import models

class Vehicle(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    driver_id = models.IntegerField(null=True, blank=True)
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    model_name = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    manufacturing_year = models.IntegerField(null=True, blank=True)
    seat_arrangement = models.IntegerField(null=True, blank=True)


    def __str__(self):
        return f"{self.manufacturer} {self.model_name}"