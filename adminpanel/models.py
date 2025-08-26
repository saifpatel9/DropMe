# adminpanel/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone # Import timezone

# Custom Manager for AdminUser
class AdminUserManager(BaseUserManager):
    def create_user(self, email, name, phone, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, phone=phone, **extra_fields)
        user.set_password(password) # Use set_password to hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'superadmin') # Set role for superuser

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, name, phone, password, **extra_fields)

class AdminUser(AbstractBaseUser, PermissionsMixin):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='adminuser_set',
        blank=True,
        help_text='The groups this admin belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='adminuser_permissions',
        blank=True,
        help_text='Specific permissions for this admin.',
        verbose_name='user permissions'
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True) # Made phone optional if not critical for every user
    # password field is handled by AbstractBaseUser
    role = models.CharField(max_length=50, default='staff') # 'superadmin', 'staff', etc.
    
    # Required fields for AbstractBaseUser and PermissionsMixin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False) # For PermissionsMixin

    date_joined = models.DateTimeField(default=timezone.now) # Add date_joined if you need it

    objects = AdminUserManager()

    USERNAME_FIELD = 'email'  # This tells Django to use email as the unique identifier for login
    REQUIRED_FIELDS = ['name', 'phone'] # Fields prompted when creating a user via createsuperuser command

    class Meta:
        db_table = 'AdminUser'
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    # PermissionsMixin requires these methods (though AbstractBaseUser handles many via its manager)
    # You might want to define specific permissions methods if your 'role' field governs them.
    # For now, PermissionsMixin provides default `has_perm`, `has_module_perms`.
    # You can customize if roles define specific permissions beyond Django's default permission system.