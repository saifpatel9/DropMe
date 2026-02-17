# driver/models.py
from django.db import models
from django.utils import timezone
from config.validators import mobile_number_validator

class Driver(models.Model):
    driver_id = models.AutoField(primary_key=True)
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    # Basic Information - matching database exactly
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(unique=True, max_length=150)  # NOT NULL in DB
    phone = models.CharField(unique=True, max_length=15, validators=[mobile_number_validator])   # NOT NULL in DB
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True, null=True)  # ENUM in DB
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    # Vehicle Information
    plate_number = models.CharField(max_length=20, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    manufacturing_year = models.IntegerField(blank=True, null=True)  # YEAR type in MySQL
    seat_arrangement = models.IntegerField(blank=True, null=True)
    
    # Address and Availability
    full_address = models.TextField(blank=True, null=True)
    availability = models.BooleanField(default=True, null=True, blank=True)  # tinyint(1) in MySQL
    
    # Payment Information
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    password_hash = models.TextField(blank=True, null=True)
    
    # Services - tinyint(1) in MySQL = BooleanField in Django
    daily_services = models.BooleanField(blank=True, null=True)
    rental_services = models.BooleanField(blank=True, null=True)
    outstation_services = models.BooleanField(blank=True, null=True)
    
    # Rating and Status
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, blank=True, null=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='Active', blank=True, null=True)  # ENUM in DB
    created_at = models.DateTimeField(auto_now_add=True)  # DEFAULT CURRENT_TIMESTAMP
    is_deleted = models.BooleanField(default=False)
    
    # Documents
    vehicle_rc = models.FileField(upload_to="driver_documents/vehicle_rcs/", null=True, blank=True)
    vehicle_rc_status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Verified", "Verified"), ("Rejected", "Rejected")],
        default="Pending"
    )

    license_document = models.FileField(upload_to="driver_documents/licenses/", null=True, blank=True)
    license_document_status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Verified", "Verified"), ("Rejected", "Rejected")],
        default="Pending"
    )

    id_proof = models.FileField(upload_to="driver_documents/id_proofs/", null=True, blank=True)
    id_proof_status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Verified", "Verified"), ("Rejected", "Rejected")],
        default="Pending"
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
