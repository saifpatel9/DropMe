from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ]
    
    # Basic Information - matching database exactly
    first_name = models.CharField(max_length=100, blank=False, null=False) 
    last_name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(unique=True, max_length=150)  # NOT NULL in DB
    password = models.CharField(max_length=128)
    phone = models.CharField(unique=True, max_length=15)   # NOT NULL in DB
    country_code = models.CharField(max_length=5, blank=True, default='+91')
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True, null=True)  # ENUM in DB
    profile_picture = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # true/false only; no null
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='Active', blank=True, null=True)  # ENUM with default 'Active'
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    referred_by = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      
    
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']

    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def id(self):
        return self.user_id