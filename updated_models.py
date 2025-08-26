# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    driver = models.ForeignKey('Driver', models.DO_NOTHING, blank=True, null=True)
    pickup_location = models.CharField(max_length=255, blank=True, null=True)
    dropoff_location = models.CharField(max_length=255, blank=True, null=True)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    drop_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    drop_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    scheduled_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=9, blank=True, null=True)
    fare = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    duration_min = models.IntegerField(blank=True, null=True)
    service_type = models.ForeignKey('Servicetype', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Booking'


class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    stars = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Feedback'


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    booking = models.ForeignKey(Booking, models.DO_NOTHING, blank=True, null=True)
    payment_mode = models.CharField(max_length=50, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Payment'


class Promocode(models.Model):
    promo_id = models.AutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    expiry_time = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    max_usage = models.IntegerField(blank=True, null=True)
    max_usage_per_user = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'PromoCode'


class Servicetype(models.Model):
    service_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    number_of_seats = models.IntegerField(blank=True, null=True)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    min_fare = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    price_per_minute = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_per_km = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mileage = models.IntegerField(blank=True, null=True)
    daily_service = models.IntegerField(blank=True, null=True)
    rental_service = models.IntegerField(blank=True, null=True)
    outstation_service = models.IntegerField(blank=True, null=True)
    provider_commission = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    admin_commission = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    driver_cash_limit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    picture = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ServiceType'


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(unique=True, max_length=150)
    phone = models.CharField(unique=True, max_length=15)
    country_code = models.CharField(max_length=5, blank=True, null=True)
    gender = models.CharField(max_length=6, blank=True, null=True)
    profile_picture = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=8, blank=True, null=True)
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    referred_by = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'User'


class Vehicle(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    driver = models.ForeignKey('Driver', models.DO_NOTHING, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    manufacturing_year = models.TextField(blank=True, null=True)  # This field type is a guess.
    seat_arrangement = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Vehicle'


class Wallet(models.Model):
    wallet_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    used_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Wallet'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BookingServicetype(models.Model):
    name = models.CharField(unique=True, max_length=50)
    booking_id = models.AutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'booking_servicetype'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Driver(models.Model):
    driver_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(unique=True, max_length=150)
    phone = models.CharField(unique=True, max_length=15)
    gender = models.CharField(max_length=6, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    plate_number = models.CharField(max_length=20, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    manufacturing_year = models.TextField(blank=True, null=True) 
    seat_arrangement = models.IntegerField(blank=True, null=True)
    full_address = models.TextField(blank=True, null=True)
    availability = models.IntegerField(blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    password_hash = models.TextField(blank=True, null=True)
    daily_services = models.IntegerField(blank=True, null=True)
    rental_services = models.IntegerField(blank=True, null=True)
    outstation_services = models.IntegerField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=8, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    license_document = models.CharField(max_length=100, blank=True, null=True)
    id_proof = models.CharField(max_length=100, blank=True, null=True)
    vehicle_rc = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'driver'


class FaqFaq(models.Model):
    id = models.BigAutoField(primary_key=True)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    main_topic = models.ForeignKey('FaqMaintopic', models.DO_NOTHING)
    sub_topic = models.ForeignKey('FaqSubtopic', models.DO_NOTHING)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'faq_faq'


class FaqMaintopic(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'faq_maintopic'


class FaqSubtopic(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    main_topic = models.ForeignKey(FaqMaintopic, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'faq_subtopic'
        unique_together = (('main_topic', 'name'),)


class Rating(models.Model):
    rating_id = models.AutoField(primary_key=True)
    passenger = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    driver = models.ForeignKey(Driver, models.DO_NOTHING, blank=True, null=True)
    booking = models.ForeignKey(Booking, models.DO_NOTHING, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    given_by = models.CharField(max_length=6, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rating'


class RentalPackage(models.Model):
    id = models.BigAutoField(primary_key=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    time_hours = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'rental_package'


class RentalService(models.Model):
    id = models.BigAutoField(primary_key=True)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2)
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2)
    per_minute_rate = models.DecimalField(max_digits=10, decimal_places=2)
    package = models.ForeignKey(RentalPackage, models.DO_NOTHING)
    service_type = models.ForeignKey(Servicetype, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'rental_service'
        unique_together = (('service_type', 'package'),)


class WalletPayment(models.Model):
    wallet_payment_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    payment = models.ForeignKey(Payment, models.DO_NOTHING, blank=True, null=True)
    payment_mode = models.CharField(max_length=50, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    user_id = models.BigIntegerField(blank=True, null=True)
    wallet = models.ForeignKey(Wallet, models.DO_NOTHING, blank=True, null=True)
    payment_ref = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wallet_payment'
