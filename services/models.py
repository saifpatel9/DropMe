from django.db import models


class ServiceType(models.Model):
    service_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    number_of_seats = models.IntegerField(null=True, blank=True)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_per_minute = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mileage = models.BooleanField(null=True, blank=True)
    daily_service = models.BooleanField(null=True, blank=True)
    rental_service = models.BooleanField(null=True, blank=True)
    outstation_service = models.BooleanField(null=True, blank=True)
    provider_commission = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    admin_commission = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    driver_cash_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    picture = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    status = models.CharField(max_length=10,choices=[('active', 'Active'), ('inactive', 'Inactive')],default='active')

    class Meta:
        db_table = 'servicetype'
        managed = True

    def __str__(self):
        return self.name


# ✅ Moved OUTSIDE ServiceType class
class RentalPackage(models.Model):
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    time_hours = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        db_table = 'rental_package'

    def __str__(self):
        return f"{self.distance_km} KM / {self.time_hours} Hours"


class RentalService(models.Model):
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    package = models.ForeignKey(RentalPackage, on_delete=models.CASCADE)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2)
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2)
    per_minute_rate = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self):
        return f"{self.service_type.name} - {self.package}"


# FareSlab model
class FareSlab(models.Model):
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='fare_slabs')

    km_from = models.DecimalField(max_digits=6, decimal_places=2)
    km_to = models.DecimalField(max_digits=6, decimal_places=2)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)
    rate_per_km = models.DecimalField(max_digits=10, decimal_places=2)
    rate_per_minute = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'fare_slab'

    def __str__(self):
        return f"{self.service_type.name} | {self.km_from} km - {self.km_to} km"