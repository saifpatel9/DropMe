from decimal import Decimal, ROUND_HALF_UP
from django.utils.timezone import localtime
from django.shortcuts import render, get_object_or_404, redirect
from .models import Driver
from booking.models import Booking, RideRequest, RidePin
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from payments.models import Payment
from django.views.decorators.http import require_POST
from driver.decorators import driver_login_required
import logging
from django.db import transaction
from rating.models import Rating
import json
from .forms import DriverEditProfileForm
from django.core.cache import cache
import random
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta

logger = logging.getLogger(__name__)

def admin_driver_list(request):
    drivers = Driver.objects.all()
    return render(request, 'adminpanel/drivers.html', {'drivers': drivers})

def admin_driver_detail(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    return render(request, 'adminpanel/driver_detail.html', {'driver': driver})

def driver_homepage_cab_view(request):
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return redirect('login')

    try:
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        return redirect('login')

    total_rides = Booking.objects.filter(driver=driver).count()
    completed_rides = Booking.objects.filter(driver=driver, status='Completed').count()
    cancelled_rides = Booking.objects.filter(driver=driver, status='Cancelled').count()
    scheduled_rides = Booking.objects.filter(driver=driver, status='Confirmed').count()

    active_booking = Booking.objects.filter(
        driver=driver,
        status__in=['Confirmed', 'Arrived', 'Ongoing']
    ).order_by('-scheduled_time', '-booking_id').first()

    confirmed_rides = Booking.objects.filter(
        driver=driver,
        status__in=['Confirmed', 'Scheduled']
    )

    # Retrieve active ride requests assigned to this driver only
    ride_requests = RideRequest.objects.filter(
        status='Requested',
        driver=driver,
        service_type__name__iexact=driver.vehicle_type
    )

    # Combine confirmed bookings and ride requests, sort properly
    def get_sort_time(ride):
        # Bookings will have scheduled_time, RideRequests may have scheduled_time or None
        return getattr(ride, 'scheduled_time', None) or getattr(ride, 'created_at', timezone.now())

    all_rides = list(confirmed_rides) + list(ride_requests)
    all_rides.sort(key=get_sort_time)

    # === Calculate earnings (today, week, month, total) ===
    completed_bookings = (
        Booking.objects.filter(driver=driver, status='Completed')
        .select_related('service_type')
        .order_by('-scheduled_time')
    )

    from datetime import timedelta

    today = localtime().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    earnings_today = Decimal("0.00")
    earnings_week = Decimal("0.00")
    earnings_month = Decimal("0.00")
    total_earnings = Decimal("0.00")

    for ride in completed_bookings:
        fare_total = Decimal(ride.fare or 0)
        service = ride.service_type

        provider_percent = Decimal(service.provider_commission or 0) / Decimal(100)
        booking_fee = Decimal(service.booking_fee or 0)
        tax_percent = Decimal(service.tax_percentage or 0) / Decimal(100)

        if tax_percent > 0:
            subtotal_before_tax = fare_total / (1 + tax_percent)
        else:
            subtotal_before_tax = fare_total

        components_excl_booking = subtotal_before_tax - booking_fee
        driver_earning = (components_excl_booking * provider_percent).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_earnings += driver_earning

        local_dt = localtime(ride.scheduled_time)
        local_date = local_dt.date()
        if local_date == today:
            earnings_today += driver_earning
        if local_date >= start_of_week:
            earnings_week += driver_earning
        if local_date >= start_of_month:
            earnings_month += driver_earning

    return render(request, 'driver/driver_homepage.html', {
        'driver': driver,
        'total_rides': total_rides,
        'completed_rides': completed_rides,
        'cancelled_rides': cancelled_rides,
        'scheduled_rides': scheduled_rides,
        'all_rides': all_rides,
        'ride_requests': ride_requests,
        'total_earnings': total_earnings,
        'earnings_today': earnings_today,
        'earnings_week': earnings_week,
        'earnings_month': earnings_month,
        'active_booking': active_booking,
    })

def accept_ride(request, ride_request_id):
    logger.debug(f"accept_ride called for ride_request_id={ride_request_id}")

    driver_id = request.session.get('driver_id')
    if not driver_id:
        logger.warning("No driver_id in session, redirecting to login")
        return redirect('driver_login')

    driver = get_object_or_404(Driver, driver_id=driver_id)

    with transaction.atomic():
        # Only allow the currently assigned driver to accept
        ride_request = get_object_or_404(
            RideRequest,
            id=ride_request_id,
            status='Requested',
            driver=driver,
            service_type__name__iexact=driver.vehicle_type
        )

        if hasattr(ride_request, 'booking') and ride_request.booking:
            logger.warning(f"RideRequest {ride_request_id} already has booking {ride_request.booking.booking_id}")
            messages.error(request, "This ride has already been accepted by another driver.")
            return redirect('driver_homepage')

        booking = Booking.objects.create(
            user=ride_request.user,
            driver=driver,
            pickup_location=ride_request.pickup_location,
            dropoff_location=ride_request.dropoff_location,
            fare=ride_request.fare,
            scheduled_time=ride_request.scheduled_time,
            payment_mode=ride_request.payment_mode,
            service_type=ride_request.service_type,
            status='Confirmed'
        )

        # Generate a unique 4-digit PIN for this booking
        pin_value = f"{random.randint(0, 9999):04d}"
        RidePin.objects.update_or_create(
            booking=booking,
            defaults={
                'pin_hash': make_password(pin_value),
                'pin_plain': pin_value,
                'attempts': 0,
                'locked_until': None,
                'is_active': True,
                'is_verified': False,
            }
        )

        ride_request.booking = booking
        ride_request.status = 'Accepted'
        ride_request.save(update_fields=['booking', 'status'])

        logger.debug(f"RideRequest {ride_request_id} accepted, Booking {booking.booking_id} created.")

    messages.success(request, f"Ride #{ride_request.id} accepted successfully.")
    
    # If AJAX request, return JSON with booking_id
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'booking_id': booking.booking_id,
            'message': f"Ride #{ride_request.id} accepted successfully."
        })
    
    return redirect('driver_homepage')

    
@csrf_exempt
def reject_ride(request, ride_request_id):
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return redirect('driver_login')

    try:
        ride_obj = RideRequest.objects.get(id=ride_request_id)
        ride_obj.status = 'Rejected'
        ride_obj.save()
    except RideRequest.DoesNotExist:
        pass

    messages.info(request, f"You rejected ride request #{ride_request_id}.")
    return redirect('driver_homepage')


def check_driver_assignment(request):
    booking_id = request.GET.get('booking_id')
    if not booking_id:
        return JsonResponse({'driver_assigned': False})

    try:
        booking = Booking.objects.select_related('driver').get(booking_id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'driver_assigned': False})

    if booking.driver:
        driver = booking.driver
        driver_name = f"{driver.first_name} {driver.last_name}" if driver.first_name and driver.last_name else driver.name
        driver_phone = getattr(driver, 'phone', "N/A")
        vehicle_info = f"{getattr(driver, 'vehicle_type', 'Unknown')} - {getattr(driver, 'vehicle_number', 'N/A')}"
        return JsonResponse({
            'driver_assigned': True,
            'driver_name': driver_name,
            'driver_phone': driver_phone,
            'vehicle_info': vehicle_info
        })
    else:
        return JsonResponse({'driver_assigned': False})
    
@driver_login_required
def driver_profile_view(request, driver_id=None):
    """
    Driver profile page with document uploads.
    Resolves the driver either from explicit `driver_id` param (admin use)
    or from the session key set by driver login.
    """
    # Prefer explicit URL param; otherwise use session-stored driver_id
    effective_id = driver_id or request.session.get("driver_id")
    if not effective_id:
        # Session expired or not logged in; let user re-authenticate
        return redirect("driver_login")

    # `driver_id` is the primary key on Driver
    driver = get_object_or_404(Driver, driver_id=effective_id)

    if request.method == "POST":
        fields_to_update = []

        if "vehicle_rc" in request.FILES:
            driver.vehicle_rc = request.FILES["vehicle_rc"]
            driver.vehicle_rc_status = "Pending"
            fields_to_update += ["vehicle_rc", "vehicle_rc_status"]

        if "license_document" in request.FILES:
            driver.license_document = request.FILES["license_document"]
            driver.license_document_status = "Pending"
            fields_to_update += ["license_document", "license_document_status"]

        if "id_proof" in request.FILES:
            driver.id_proof = request.FILES["id_proof"]
            driver.id_proof_status = "Pending"
            fields_to_update += ["id_proof", "id_proof_status"]

        if fields_to_update:
            driver.save(update_fields=fields_to_update)

        # Redirect back to the same page (works whether URL has driver_id or not)
        return redirect(request.path)

    return render(request, "driver/driver_profile.html", {"driver": driver})

@driver_login_required
def driver_rides_view(request):
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return redirect('unified_login')
    try:
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        return redirect('unified_login')

    # Only show completed rides
    completed_rides = Booking.objects.filter(
        driver=driver,
        status='Completed'
    ).order_by('-scheduled_time')

    context = {
        'completed_rides': completed_rides,
    }
    return render(request, 'driver/driver_rides.html', context)


@require_POST
@driver_login_required
def arrived_ride_view(request, booking_id):
    """
    Mark that the driver has arrived at the pickup location for a booking.
    Uses cache to signal passenger side without DB schema change.
    """
    driver_id = request.session.get('driver_id')
    if not driver_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        return redirect('unified_login')
    try:
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Driver not found'}, status=404)
        return redirect('unified_login')

    booking = get_object_or_404(Booking, booking_id=booking_id, driver=driver)
    # Only allow arrival announcement before ride start
    if booking.status in ['Confirmed', 'Scheduled']:
        # Persist status change to 'Arrived'
        booking.status = 'Arrived'
        booking.save(update_fields=['status'])
        cache_key = f"booking:{booking.booking_id}:arrived"
        cache.set(cache_key, True, timeout=60 * 60)  # 1 hour TTL
        
        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Arrival notified for booking #{booking.booking_id}.',
                'booking_id': booking.booking_id,
                'status': 'Arrived'
            })
        
        messages.success(request, f"Arrival notified for booking #{booking.booking_id}.")
    else:
        error_msg = "Arrival can only be marked before the ride starts."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, error_msg)
    
    return redirect('driver_rides')

# Removed driver_ride_request_page view - ride requests are now handled directly on the driver dashboard
# The ride request functionality is integrated into driver_homepage_cab_view via AJAX and popups

def api_assigned_requests(request):
    """
    Lightweight API that returns the list of RideRequest IDs currently assigned to the
    authenticated driver. Used by client-side polling to auto-hide reassigned requests.
    """
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return JsonResponse({'assigned_request_ids': []})
    try:
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        return JsonResponse({'assigned_request_ids': []})
    ids = list(
        RideRequest.objects
        .filter(status='Requested', driver=driver)
        .values_list('id', flat=True)
    )
    return JsonResponse({'assigned_request_ids': ids})

@driver_login_required
def api_ride_request_details(request, ride_request_id):
    """
    API endpoint to fetch full details of a ride request for the popup notification.
    """
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        driver = Driver.objects.get(driver_id=driver_id)
        # Allow fetching both Requested and Accepted ride requests
        ride_request = RideRequest.objects.get(
            id=ride_request_id,
            driver=driver
        )
        
        # Get passenger rating
        from rating.models import Rating
        from django.db.models import Avg
        passenger_rating = Rating.objects.filter(
            User_id=ride_request.user_id,
            given_by='driver'
        ).aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        passenger_name = f"{ride_request.user.first_name} {ride_request.user.last_name}".strip()
        if not passenger_name:
            passenger_name = ride_request.user.email.split('@')[0]
        
        # Ensure coordinates are valid numbers or None
        pickup_lat = float(ride_request.pickup_latitude) if ride_request.pickup_latitude is not None else None
        pickup_lng = float(ride_request.pickup_longitude) if ride_request.pickup_longitude is not None else None
        dropoff_lat = float(ride_request.drop_latitude) if ride_request.drop_latitude is not None else None
        dropoff_lng = float(ride_request.drop_longitude) if ride_request.drop_longitude is not None else None
        
        response_data = {
            'id': ride_request.id,
            'passengerName': passenger_name,
            'rating': round(float(passenger_rating), 1) if passenger_rating else 4.5,
            'pickup': ride_request.pickup_location,
            'dropoff': ride_request.dropoff_location,
            'pickupLat': pickup_lat,
            'pickupLng': pickup_lng,
            'dropoffLat': dropoff_lat,
            'dropoffLng': dropoff_lng,
            'fare': str(ride_request.fare),
            'serviceType': ride_request.service_type.name if ride_request.service_type else 'Standard',
            'paymentMode': ride_request.payment_mode or 'Cash',
            'createdAt': ride_request.created_at.isoformat()
        }
        
        # Include booking_id if the ride has been accepted
        if hasattr(ride_request, 'booking') and ride_request.booking:
            response_data['booking_id'] = ride_request.booking.booking_id
        
        return JsonResponse(response_data)
    except RideRequest.DoesNotExist:
        return JsonResponse({'error': 'Ride request not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching ride request details: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@driver_login_required
def api_booking_details(request, booking_id):
    """
    API endpoint to fetch booking details with coordinates for route display.
    """
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        driver = Driver.objects.get(driver_id=driver_id)
        booking = Booking.objects.get(
            booking_id=booking_id,
            driver=driver
        )
        
        response_data = {
            'booking_id': booking.booking_id,
            'pickup_location': booking.pickup_location,
            'dropoff_location': booking.dropoff_location,
            'pickup_latitude': float(booking.pickup_latitude) if booking.pickup_latitude else None,
            'pickup_longitude': float(booking.pickup_longitude) if booking.pickup_longitude else None,
            'drop_latitude': float(booking.drop_latitude) if booking.drop_latitude else None,
            'drop_longitude': float(booking.drop_longitude) if booking.drop_longitude else None,
            'status': booking.status,
            'fare': str(booking.fare) if booking.fare else None,
        }
        
        return JsonResponse(response_data)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching booking details: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@require_POST
@driver_login_required
def end_ride_view(request, booking_id):
    driver_id = request.session.get('driver_id')
    if not driver_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        return redirect('unified_login')
    try:
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Driver not found'}, status=404)
        return redirect('unified_login')

    booking = get_object_or_404(Booking, booking_id=booking_id, driver=driver)
    if booking.status == 'Ongoing':
        booking.status = 'Completed'
        booking.save()

        payment_mode = booking.payment_mode or "Cash"  # default if somehow null

        # ✅ Create Payment record with passenger-selected payment mode
        Payment.objects.create(
            user=booking.user,
            booking=booking,
            payment_mode=payment_mode,
            amount=booking.fare,
            status='completed' if payment_mode.lower() == 'cash' else 'completed'
        )

        # Ensure PIN is invalidated once ride is completed
        ride_pin = getattr(booking, 'ride_pin', None)
        if ride_pin:
            ride_pin.is_active = False
            ride_pin.pin_plain = ''
            ride_pin.save(update_fields=['is_active', 'pin_plain'])

        # Return JSON for AJAX requests with complete ride details for popup
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Get passenger name
            passenger_name = ""
            if booking.user:
                passenger_name = f"{booking.user.first_name} {booking.user.last_name}".strip()
                if not passenger_name:
                    passenger_name = booking.user.email.split('@')[0] if booking.user.email else "Passenger"
            
            # Extract first part of location (before first comma)
            pickup_location_short = booking.pickup_location.split(',')[0].strip() if booking.pickup_location else "N/A"
            dropoff_location_short = booking.dropoff_location.split(',')[0].strip() if booking.dropoff_location else "N/A"
            
            return JsonResponse({
                'success': True,
                'message': f'Ride #{booking.booking_id} marked as completed and payment recorded.',
                'booking_id': booking.booking_id,
                'status': 'Completed',
                'passengerName': passenger_name,
                'pickup': pickup_location_short,
                'dropoff': dropoff_location_short,
                'pickupFull': booking.pickup_location or '',
                'dropoffFull': booking.dropoff_location or '',
                'fare': str(booking.fare) if booking.fare else '0.00',
                'distance': str(booking.distance_km) if booking.distance_km else None,
                'duration': booking.duration_min if booking.duration_min else None,
                'serviceType': booking.service_type.name if booking.service_type else 'Standard',
                'paymentMode': payment_mode
            })
        
        messages.success(request, f"Ride #{booking.booking_id} marked as completed and payment recorded.")
    else:
        error_msg = "You can only complete an ongoing ride."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, error_msg)
    return redirect('driver_rides')


@require_POST
@driver_login_required
def verify_ride_pin(request, booking_id):
    """
    Verify the passenger-shared 4-digit PIN before allowing ride start.
    Enforces retry limits and temporary lockout.
    """
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

    try:
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Driver not found'}, status=404)

    try:
        booking = Booking.objects.get(booking_id=booking_id, driver=driver)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found or not assigned to you'}, status=404)

    ride_pin = getattr(booking, 'ride_pin', None)
    if not ride_pin or not ride_pin.is_active:
        return JsonResponse({'success': False, 'error': 'PIN not available or already used'}, status=400)

    # Check lockout
    now = timezone.now()
    if ride_pin.locked_until and ride_pin.locked_until > now:
        remaining = int((ride_pin.locked_until - now).total_seconds() // 60) + 1
        return JsonResponse({
            'success': False,
            'error': f'PIN verification locked. Try again in {remaining} min.',
            'locked': True,
            'locked_until': ride_pin.locked_until.isoformat()
        }, status=423)

    pin_input = request.POST.get('pin', '').strip()
    if not pin_input.isdigit() or len(pin_input) != 4:
        return JsonResponse({'success': False, 'error': 'Enter a valid 4-digit PIN.'}, status=400)

    # Log attempt
    logger.info(f"[PIN VERIFY] driver={driver.driver_id} booking={booking_id} attempt_pin={pin_input}")

    if check_password(pin_input, ride_pin.pin_hash):
        ride_pin.is_verified = True
        ride_pin.attempts = 0
        ride_pin.locked_until = None
        ride_pin.save(update_fields=['is_verified', 'attempts', 'locked_until'])
        return JsonResponse({'success': True, 'message': 'PIN verified. You can start the ride now.'})

    # Failed attempt handling
    ride_pin.attempts += 1
    attempts_left = max(0, 3 - ride_pin.attempts)
    if ride_pin.attempts >= 3:
        ride_pin.locked_until = now + timedelta(minutes=5)
        ride_pin.attempts = 0
        ride_pin.save(update_fields=['locked_until', 'attempts'])
        return JsonResponse({
            'success': False,
            'error': 'Too many attempts. PIN verification locked for 5 minutes.',
            'locked': True,
            'locked_until': ride_pin.locked_until.isoformat()
        }, status=423)

    ride_pin.save(update_fields=['attempts'])
    return JsonResponse({
        'success': False,
        'error': 'Invalid PIN. Please ask the passenger for the correct code.',
        'attempts_left': attempts_left
    }, status=400)


@require_POST
@driver_login_required
def start_ride_view(request, booking_id):
    driver_id = request.session.get('driver_id')
    if not driver_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        return redirect('unified_login')
    
    try:
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Driver not found'}, status=404)
        return redirect('unified_login')

    booking = get_object_or_404(Booking, booking_id=booking_id, driver=driver)

    # Enforce PIN verification before starting
    ride_pin = getattr(booking, 'ride_pin', None)
    if ride_pin:
        if not ride_pin.is_verified:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'PIN verification required before starting ride.'}, status=403)
            messages.error(request, 'PIN verification required before starting ride.')
            return redirect('driver_rides')
    else:
        logger.warning(f"[PIN VERIFY] Missing ride pin for booking {booking.booking_id}")

    if booking.status in ['Confirmed', 'Arrived']:
        booking.status = 'Ongoing'
        booking.save()

        # Invalidate PIN once ride starts
        if ride_pin:
            ride_pin.is_active = False
            ride_pin.pin_plain = ''
            ride_pin.save(update_fields=['is_active', 'pin_plain'])
        
        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Include booking coordinates for route drawing
            response_data = {
                'success': True,
                'message': f'Ride #{booking.booking_id} started.',
                'booking_id': booking.booking_id,
                'status': 'Ongoing',
                'pickup_location': booking.pickup_location,
                'dropoff_location': booking.dropoff_location,
                'pickup_latitude': float(booking.pickup_latitude) if booking.pickup_latitude else None,
                'pickup_longitude': float(booking.pickup_longitude) if booking.pickup_longitude else None,
                'drop_latitude': float(booking.drop_latitude) if booking.drop_latitude else None,
                'drop_longitude': float(booking.drop_longitude) if booking.drop_longitude else None,
            }
            return JsonResponse(response_data)
        
        messages.success(request, f"Ride #{booking.booking_id} started.")
    else:
        error_msg = "Only confirmed or arrived rides can be started."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, error_msg)

    return redirect('driver_rides')


@driver_login_required
def driver_earnings_view(request):
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return redirect('unified_login')
    try:
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        return redirect('unified_login')

    today = localtime().date()
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)

    all_completed_rides = Booking.objects.filter(
        driver=driver,
        status='Completed'
    ).order_by('-scheduled_time')

    print("=== [DEBUG] Completed Rides for Driver Earnings Calculation ===")
    earnings_today = Decimal("0.00")
    earnings_month = Decimal("0.00")
    earnings_year = Decimal("0.00")

    ride_data = []

    for ride in all_completed_rides:
        utc_dt = ride.scheduled_time
        local_dt = localtime(utc_dt)
        local_date = local_dt.date()

        fare_total = Decimal(ride.fare or 0)
        service = ride.service_type

        provider_percent = Decimal(service.provider_commission or 0) / Decimal(100)
        admin_percent = Decimal(service.admin_commission or 0) / Decimal(100)
        booking_fee = Decimal(service.booking_fee or 0)
        tax_percent = Decimal(service.tax_percentage or 0) / Decimal(100)

        if tax_percent > 0:
            subtotal_before_tax = fare_total / (1 + tax_percent)
        else:
            subtotal_before_tax = fare_total

        components_excl_booking = subtotal_before_tax - booking_fee
        driver_earning = (components_excl_booking * provider_percent).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        print(
            f"Ride ID: {ride.booking_id}, "
            f"Scheduled (UTC): {utc_dt}, Local Date: {local_date}, "
            f"Fare: {fare_total}, Provider%: {provider_percent}, "
            f"Admin%: {admin_percent}, Driver Earning: {driver_earning}"
        )

        if local_date == today:
            earnings_today += driver_earning
        if local_date >= start_of_month:
            earnings_month += driver_earning
        if local_date >= start_of_year:
            earnings_year += driver_earning

        ride_data.append({
            'booking_id': ride.booking_id,
            'pickup_location': ride.pickup_location,
            'dropoff_location': ride.dropoff_location,
            'scheduled_time': ride.scheduled_time,
            'fare': fare_total,
            'driver_earning': driver_earning
        })

    print("===============================================================")
    print(f"[DEBUG] earnings_today: {earnings_today}")
    print(f"[DEBUG] earnings_month: {earnings_month}")
    print(f"[DEBUG] earnings_year: {earnings_year}")

    context = {
        'earnings_today': earnings_today,
        'earnings_month': earnings_month,
        'earnings_year': earnings_year,
        'driver': driver,
        'ride_earnings': ride_data,
    }
    return render(request, 'driver/driver_earnings.html', context)

@require_POST
@driver_login_required
def toggle_availability(request):
    """Toggle driver availability status"""
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)

    try:
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        return JsonResponse({"success": False, "error": "Driver not found"}, status=404)

    # Handle both AJAX and regular form submissions
    content_type = request.META.get('CONTENT_TYPE', '')
    
    if 'application/json' in content_type:
        # Handle JSON request
        try:
            data = json.loads(request.body)
            new_availability = data.get('availability')
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    else:
        # Handle form-encoded request
        availability_str = request.POST.get('availability', '').lower()
        new_availability = availability_str in ['true', '1', 'on']

    # Update driver availability
    driver.availability = new_availability
    driver.save()

    return JsonResponse({
        "success": True, 
        "availability": driver.availability,
        "status_text": "Available" if driver.availability else "Unavailable"
    })

@driver_login_required
def driver_rating_page(request):
    try:
        # Get the driver instance from session, not from request.user
        driver_id = request.session.get('driver_id')
        driver = get_object_or_404(Driver, pk=driver_id)
    except Driver.DoesNotExist:
        messages.error(request, "Driver profile not found.")
        return redirect('homepage')  # or driver dashboard
    
    # Get all completed bookings for this driver
    completed_bookings = (
        Booking.objects.filter(driver=driver, status='Completed')
        .select_related('user', 'service_type')
    )
    
    # Get existing ratings given by this driver
    existing_ratings = (
        Rating.objects.filter(driver=driver, given_by='driver')
        .select_related('booking', 'User')  # changed passenger → User if your model uses that
    )
    
    # Create a mapping of booking_id to rating for quick lookup
    ratings_map = {rating.booking_id: rating for rating in existing_ratings}
    
    # Separate rated and unrated bookings
    unrated_bookings = []
    rated_bookings = []
    
    for booking in completed_bookings:
        if booking.booking_id in ratings_map:
            # Attach rating object for template access
            booking.rating_obj = ratings_map[booking.booking_id]
            rated_bookings.append(booking)
        else:
            unrated_bookings.append(booking)
    
    context = {
        'driver': driver,
        'unrated_bookings': unrated_bookings,
        'rated_bookings': rated_bookings,
        'total_completed': completed_bookings.count(),
        'total_unrated': len(unrated_bookings),
        'total_rated': len(rated_bookings),
    }
    
    return render(request, 'driver/driver_rating.html', context)

@driver_login_required
@require_POST
def submit_driver_rating(request):
    """
    Handle driver rating submission for a specific booking.
    """
    driver_id = request.session.get('driver_id')
    if not driver_id:
        return JsonResponse({'success': False, 'message': 'Driver not logged in.'})
    
    try:
        from driver.models import Driver
        driver = Driver.objects.get(driver_id=driver_id)
    except Driver.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Driver profile not found.'})
    
    booking_id = request.POST.get('booking_id')
    rating_value = request.POST.get('rating')
    comments = request.POST.get('comments', '').strip()
    
    if not booking_id or not rating_value:
        return JsonResponse({'success': False, 'message': 'Booking ID and rating are required.'})
    
    try:
        rating_value = int(rating_value)
        if rating_value < 1 or rating_value > 5:
            raise ValueError("Rating must be between 1 and 5")
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Invalid rating value.'})
    
    # Ensure booking belongs to this driver and is completed
    try:
        booking = Booking.objects.get(
            booking_id=booking_id, 
            driver=driver, 
            status='Completed'
        )
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Booking not found or not authorized.'})
    
    # Prevent duplicate ratings
    existing_rating = Rating.objects.filter(
        booking=booking,
        driver=driver,
        given_by='driver'
    ).first()
    
    if existing_rating:
        return JsonResponse({'success': False, 'message': 'You have already rated this ride.'})
    
    # Create the rating
    try:
        Rating.objects.create(
            booking=booking,
            User=booking.user,   
            driver=driver,
            rating=rating_value,
            comments=comments,
            given_by='driver'
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Rating submitted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error saving rating: {str(e)}'})

    
def driver_edit_profile_view(request):
    driver_id = request.session.get("driver_id")
    if not driver_id:
        return redirect("login")

    driver = get_object_or_404(Driver, pk=driver_id)

    if request.method == "POST":
        form = DriverEditProfileForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("driver:driver_profile", driver_id=driver.driver_id)
    else:
        form = DriverEditProfileForm(instance=driver)

    return render(request, "driver/driver_edit_profile.html", {"form": form, "driver": driver})