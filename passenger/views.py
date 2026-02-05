from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, PaymentMethodForm
from adminpanel.forms import PassengerForm
from decimal import Decimal
import math
from services.models import RentalPackage
from services.models import FareSlab
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rating.models import Rating
from driver.models import Driver
from booking.models import Booking
from booking.models import RideRequest, RidePin
from django.contrib.auth import logout
from faq.models import MainTopic, SubTopic, FAQ
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from services.models import ServiceType
from .ride_rules import (
    build_meta,
    derive_ride_type,
    get_outstation_disallowed,
    get_outstation_threshold_km,
    is_vehicle_allowed,
    parse_decimal,
)
from promo.models import PromoCode
from django.views.decorators.http import require_POST
import json
from .forms import EmergencyContactForm
from django.core.cache import cache
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

@login_required
def passenger_dashboard(request):
    """
    Unified passenger dashboard that handles all ride states in a single page.
    """
    # Check if user has an active ride
    active_booking = None
    active_ride_request = None
    current_state = 'booking'  # Default state
    
    # Check for active booking (Confirmed, Arrived, or Ongoing)
    active_booking = Booking.objects.filter(
        user=request.user,
        status__in=['Confirmed', 'Arrived', 'Ongoing']
    ).order_by('-booking_id').first()
    
    if active_booking:
        if active_booking.status == 'Confirmed':
            current_state = 'confirmed'
        elif active_booking.status == 'Arrived':
            current_state = 'driver_arrived'
        elif active_booking.status == 'Ongoing':
            current_state = 'ride_started'
    
    # Check for pending ride request (waiting for driver)
    if not active_booking:
        active_ride_request = RideRequest.objects.filter(
            user=request.user,
            status='Requested'
        ).order_by('-id').first()
        
        if active_ride_request:
            # Check if it has a booking
            if hasattr(active_ride_request, 'booking') and active_ride_request.booking:
                active_booking = active_ride_request.booking
                current_state = 'confirmed'
            else:
                current_state = 'waiting_for_driver'
    
    # Get rental packages for the booking form
    rental_packages = RentalPackage.objects.all()
    
    context = {
        'active_booking': active_booking,
        'active_ride_request': active_ride_request,
        'current_state': current_state,
        'rental_packages': rental_packages,
    }
    
    return render(request, 'passenger/dashboard.html', context) 

def homepage_cab_view(request):
    rental_packages = RentalPackage.objects.all()
    return render(request, 'passenger/HomepageCab.html', {
        'rental_packages': rental_packages,
        'outstation_distance_km': get_outstation_threshold_km(),
    })

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        print("📨 POST data received")

        if form.is_valid():
            print("✅ Form is valid")
            user = form.save()
            print(f"🙋‍♂️ User created: {user}")
            return redirect('login')  
        else:
            print("❌ Form is invalid")
            print(form.errors)
    else:
        form = SignupForm()
    
    return render(request, 'passenger/signup.html', {'form': form})

# Manually defined distances between location pairs (for testing)
STATIC_DISTANCES = {
    ('Dwarka', 'CBS'): 4,
    ('CBS', 'Mumbai Naka'): 6,
    ('Mumbai Naka', 'Nashik Road'): 12,
    ('College Road', 'Nashik Road'): 16,
    ('Nashik', 'Mumbai'): 200,
}

@csrf_exempt
def choose_ride_view(request):
    pickup = request.GET.get('pickup')
    dropoff = request.GET.get('dropoff')
    pickup_lat = request.GET.get('pickup_lat')
    pickup_lng = request.GET.get('pickup_lng')
    drop_lat = request.GET.get('drop_lat')
    drop_lng = request.GET.get('drop_lng')
    pickup_city = request.GET.get('pickup_city')
    pickup_district = request.GET.get('pickup_district')
    pickup_state = request.GET.get('pickup_state')
    drop_city = request.GET.get('drop_city')
    drop_district = request.GET.get('drop_district')
    drop_state = request.GET.get('drop_state')
    dynamic_distance_km = request.GET.get('distance_km')
    dynamic_duration_min = request.GET.get('duration_min')
    ride_date = request.GET.get('date')
    ride_time = request.GET.get('time')
    ride_type = request.GET.get('ride_type', 'daily') 
    estimated_fares = []
    outstation_disallowed = get_outstation_disallowed()
    outstation_threshold_km = get_outstation_threshold_km()
    ride_type_notice = None
    
    # Coordinates are optional here; distance must come from routing (frontend).

    SERVICE_DETAILS = {
        'Hatchback': {
            'icon': 'fas fa-car-side',
            'description': 'Comfy hatchback at pocket-friendly fares',
            'default_seats': 4
        },
        'Auto': {
            'icon': 'fas fa-taxi',  
            'description': 'Quick and affordable auto ride',
            'default_seats': 3
        },
        'Bike': {
            'icon': 'fas fa-motorcycle',
            'description': 'Solo rides for fast and cheap travel',
            'default_seats': 1
        },
        'Sedan': {
            'icon': 'fas fa-car',
            'description': 'Stylish sedan for a smooth ride',
            'default_seats': 4
        },
        'SUV': {
            'icon': 'fas fa-shuttle-van',
            'description': 'Spacious SUV for family trips',
            'default_seats': 7
        },
    }

    if pickup and dropoff:
        # Route distance/duration must come from frontend routing (single source of truth).
        distance = parse_decimal(dynamic_distance_km)
        duration_minutes = parse_decimal(dynamic_duration_min)
        
        # No backend fallback distance; routing distance is the single source of truth.
        time_minutes = None
        if distance is None or duration_minutes is None:
            ride_type_notice = "Unable to calculate route distance. Please select suggested locations and try again."
            print(f"[DEBUG] Missing route distance/duration. distance_km={dynamic_distance_km} duration_min={dynamic_duration_min} pickup={pickup} dropoff={dropoff}")

        pickup_meta = build_meta(pickup_city, pickup_district, pickup_state)
        drop_meta = build_meta(drop_city, drop_district, drop_state)
        derived = derive_ride_type(
            ride_type,
            pickup_meta,
            drop_meta,
            distance,
            threshold_km=outstation_threshold_km,
        )
        derived_ride_type = derived["ride_type"]
        if derived_ride_type != ride_type:
            if derived["reason"] == "distance" and distance is not None:
                ride_type_notice = f"Route distance is {distance} km, so ride type was switched to Outstation."
            else:
                ride_type_notice = "Pickup and dropoff appear to be in different areas. Ride type was switched to Outstation."
        ride_type = derived_ride_type

        if ride_type == 'rental' and request.GET.get('rental_duration_id'):
            try:
                rental_duration = request.GET.get('rental_duration_id')
                print(f"[DEBUG] Rental Duration ID received: {rental_duration}")
                rental_package = RentalPackage.objects.get(id=rental_duration)
                print(f"[DEBUG] Rental Package fetched: {rental_package}")
                from services.models import RentalService
                rental_services = RentalService.objects.filter(package=rental_package).select_related('service_type')
                estimated_fares = []

                duration_minutes = rental_package.time_hours * Decimal(60)
                distance = rental_package.distance_km
                print(f"[DEBUG] Calculated duration_minutes: {duration_minutes}, Distance: {distance}")

                for rs in rental_services:
                    service = rs.service_type
                    subtotal = (
                        rs.base_fare +
                        rs.booking_fee +
                        (distance * rs.per_km_rate) +
                        (duration_minutes * rs.per_minute_rate)
                    )
                    total_fare = Decimal(math.ceil(subtotal + (subtotal * Decimal('0.05'))))
                    icon_class = SERVICE_DETAILS.get(service.name, {}).get('icon', 'fas fa-car')

                    estimated_fares.append({
                        'service_name': service.name,
                        'number_of_seats': service.number_of_seats,
                        'estimated_price': total_fare,
                        'icon': icon_class,
                        'description': SERVICE_DETAILS.get(service.name, {}).get('description', '')
                    })
            except RentalPackage.DoesNotExist:
                rental_services = []
                estimated_fares = []
        elif distance and duration_minutes is not None:
            time_minutes = duration_minutes
            if ride_type == 'outstation':
                services = ServiceType.objects.exclude(name__in=outstation_disallowed)
                for service in services:
                    base_fare = service.base_fare or Decimal('0')
                    per_km_rate = service.price_per_km or Decimal('0')
                    per_minute_rate = service.price_per_minute or Decimal('0')
                    booking_fee = service.booking_fee or Decimal('0')
                    toll_fee = Decimal('0')  # Set toll_fee to zero
                    discount = Decimal('0')  # Set discount to zero
                    surge_charge = Decimal('0')

                    estimated_price = (
                        base_fare +
                        (distance * per_km_rate) +
                        (time_minutes * per_minute_rate) +
                        surge_charge +
                        toll_fee +
                        booking_fee -
                        discount
                    )
                    estimated_price_with_tax = estimated_price + (estimated_price * Decimal('0.05'))
                    estimated_price = Decimal(math.ceil(estimated_price_with_tax))

                    service_info = SERVICE_DETAILS.get(service.name, {})
                    model_description = getattr(service, 'description', None)
                    description = model_description if model_description else service_info.get('description', '')
                    icon = service_info.get('icon', 'fas fa-car')
                    seats = service.number_of_seats or service_info.get('default_seats', 4)

                    estimated_fares.append({
                        'service_name': service.name,
                        'estimated_price': estimated_price,
                        'number_of_seats': seats,
                        'icon': icon,
                        'description': description,
                    })
            else:
                services = ServiceType.objects.all()
                for service in services:
                    applicable_slab = FareSlab.objects.filter(
                        service_type=service,
                        km_from__lte=distance,
                        km_to__gte=distance
                    ).first()

                    if applicable_slab:
                        base_fare = applicable_slab.base_fare or Decimal('0')
                        per_km_rate = applicable_slab.rate_per_km or Decimal('0')
                        per_minute_rate = applicable_slab.rate_per_minute or Decimal('0')
                    else:
                        base_fare = service.base_fare or Decimal('0')
                        per_km_rate = service.price_per_km or Decimal('0')
                        per_minute_rate = service.price_per_minute or Decimal('0')

                    booking_fee = service.booking_fee or Decimal('0')
                    toll_fee = Decimal('0')
                    discount = Decimal('0')
                    surge_charge = Decimal('0')

                    subtotal = (
                        base_fare +
                        (distance * per_km_rate) +
                        (time_minutes * per_minute_rate) +
                        booking_fee +
                        surge_charge +
                        toll_fee -
                        discount
                    )
                    estimated_price = subtotal
                    estimated_price_with_tax = estimated_price + (estimated_price * Decimal('0.05'))
                    estimated_price = Decimal(math.ceil(estimated_price_with_tax))

                    min_fare = service.min_fare or Decimal('0')
                    if estimated_price < min_fare:
                        estimated_price = min_fare

                    service_info = SERVICE_DETAILS.get(service.name, {})
                    model_description = getattr(service, 'description', None)
                    description = model_description if model_description else service_info.get('description', '')
                    icon = service_info.get('icon', 'fas fa-car')
                    seats = service.number_of_seats or service_info.get('default_seats', 4)

                    estimated_fares.append({
                        'service_name': service.name,
                        'estimated_price': estimated_price,
                        'number_of_seats': seats,
                        'icon': icon,
                        'description': description,
                    })
        else:
            messages.error(request, f"No distance defined for route: {pickup} to {dropoff}")

    # For rental, expose RentalPackage and selected_package_id in context
    if ride_type == 'rental':
        from services.models import RentalService
        selected_package_id = request.GET.get('rental_duration_id')
        if selected_package_id:
            try:
                package = RentalPackage.objects.get(id=selected_package_id)
                rental_services = RentalService.objects.filter(package=package).select_related('service_type')
                services_list = [rental.service_type for rental in rental_services]
            except RentalPackage.DoesNotExist:
                services_list = []
        else:
            services_list = []
    else:
        services_list = ServiceType.objects.all() if pickup and dropoff else []

    rental_options = RentalPackage.objects.all() if ride_type == 'rental' else []

    context = {
        'pickup': pickup,
        'dropoff': dropoff,
        'pickup_lat': pickup_lat,
        'pickup_lng': pickup_lng,
        'drop_lat': drop_lat,
        'drop_lng': drop_lng,
        'distance_km': dynamic_distance_km or '',
        'duration_min': dynamic_duration_min or '',
        'pickup_city': pickup_city,
        'pickup_district': pickup_district,
        'pickup_state': pickup_state,
        'drop_city': drop_city,
        'drop_district': drop_district,
        'drop_state': drop_state,
        'ride_date': ride_date,
        'ride_time': ride_time,
        'ride_type': ride_type,
        'ride_type_notice': ride_type_notice,
        'estimated_fares': estimated_fares,
        'services': estimated_fares,  
        'rental_packages': RentalPackage.objects.all() if ride_type == 'rental' else [],
        'selected_package_id': int(selected_package_id) if ride_type == 'rental' and selected_package_id else None,
        'rental_options': rental_options,
        'outstation_distance_km': outstation_threshold_km,
        'outstation_disallowed_csv': ",".join(outstation_disallowed),
    }
    return render(request, 'passenger/choose_ride.html', context)

@login_required
def profile_page(request, section=None):
    if section:
        return profile_section(request, section)
    return render(request, 'passenger/profile_page.html', {
        'section_template': None
    })

@login_required
def profile_section(request, section):
    user = request.user
    section_key = section.replace('_', '-')
    context = {}
    section_template = None

    if section_key == 'personal-info':
        print("[DEBUG] Loading personal-info section")
        if request.method == 'POST':
            form = PassengerForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                print("[DEBUG] Personal info updated successfully")
                return redirect('profile_section', section='personal-info')
        else:
            form = PassengerForm(instance=user)
        section_template = 'passenger/partials/personal_info.html'
        context.update({'form': form, 'user': user})

    elif section_key == 'emergency-contact':
        print("[DEBUG] Loading emergency-contact section")
        from .forms import EmergencyContactForm

        if request.method == "POST":
            form = EmergencyContactForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                success_message = "Emergency contact saved successfully!"
            else:
                success_message = None
        else:
            form = EmergencyContactForm(instance=user)
            success_message = None

        section_template = 'passenger/partials/emergency_contact.html'
        context.update({
            'form': form,
            'success_message': success_message
        })

    elif section_key == 'my-rides':
        print("[DEBUG] Loading my-rides section")
        from booking.models import Booking
        rides = Booking.objects.filter(user=user).order_by('-booking_id')
        section_template = 'passenger/partials/my_rides.html'
        context.update({'rides': rides})

    elif section_key == 'payment':
        print("[DEBUG] Loading payment section")
        # Create form instance with current user data for proper pre-selection
        form = PaymentMethodForm(instance=user)
        section_template = 'passenger/partials/user_payment.html'
        context.update({
            'form': form,
            'selected_method': getattr(user, 'payment_method', None),
        })

    elif section_key == 'safety':
        print("[DEBUG] Loading safety section")
        section_template = 'passenger/partials/safety.html'

    elif section_key == 'delete-account':
        print("[DEBUG] Loading delete-account section")
        section_template = 'passenger/partials/delete_account.html'

    elif section_key == 'rating-and-feedback':
        print("[DEBUG] Loading rating-and-feedback section")
        from rating.models import Rating
        from booking.models import Booking 

        # Completed rides for this user
        completed_rides = (
            Booking.objects
            .filter(user=user, status="Completed")
            .order_by("-booking_id")                  
        )

        # Ratings this passenger gave to drivers
        passenger_ratings = (
            Rating.objects
            .filter(User=user, given_by="user")      
            .select_related("driver", "booking")
            .order_by("-created_at")
        )
        # Use Booking PKs for the comparison
        rated_booking_pks = passenger_ratings.values_list('booking_id', flat=True)
        rides_without_rating = completed_rides.exclude(pk__in=rated_booking_pks)

        section_template = 'passenger/partials/rating_feedback.html'
        context.update({
            'passenger_ratings': passenger_ratings,   
            'rides_without_rating': rides_without_rating,  
        })

    else:
        print(f"[DEBUG] Unknown profile section requested: {section}")
        section_template = 'passenger/partials/not_found.html'
        context.update({'section': section})

    # Always render the profile page with the correct partial
    context['section_template'] = section_template
    return render(request, 'passenger/profile_page.html', context)

@login_required
def update_payment_method(request):
  
    user = request.user
    
    if request.method == "POST":
        form = PaymentMethodForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment method updated successfully.")
            print(f"[DEBUG] Payment method updated for user {user.email}: {form.cleaned_data['payment_method']}")
        else:
            messages.error(request, "There was an error updating your payment method.")
            print(f"[DEBUG] Payment method form errors: {form.errors}")
        
        # Redirect back to the payment section to show the updated selection
        return redirect('profile_section', section='payment')
    
    # For GET requests, redirect to the payment section
    return redirect('profile_section', section='payment')

@login_required
@require_POST
def update_safety_preferences(request):
    emergency_contact = request.POST.get('emergency_contact')
    share_status = request.POST.get('share_status') == 'on'

    user = request.user
    user.emergency_contact = emergency_contact
    user.share_status = share_status
    user.save()

    print(f"[DEBUG] Safety preferences updated: Emergency Contact = {emergency_contact}, Share Status = {share_status}")
    return JsonResponse({'success': True, 'message': 'Safety preferences updated successfully.'})

@login_required
@require_POST
def submit_rating(request, booking_id):
    passenger = request.user
    rating_raw = request.POST.get("rating")
    feedback_text = request.POST.get("comments", "")

    if not rating_raw:
        messages.error(request, "Rating is required.")
        return redirect('profile_section', section='rating-and-feedback')

    try:
        rating_value = int(rating_raw)
    except (TypeError, ValueError):
        messages.error(request, "Invalid rating value.")
        return redirect('profile_section', section='rating-and-feedback')

    # IMPORTANT: booking_id here is the Booking PK (because we now post ride.pk from the template)
    booking = get_object_or_404(Booking, pk=booking_id, user=passenger)

    rating_obj, created = Rating.objects.update_or_create(
        booking=booking,
        User=request.user,  
        driver=booking.driver,  # can be None; allowed by your model
        defaults={
            "rating": rating_value,
            "comments": feedback_text,
            "given_by": "user",
            # don't pass created_at; auto_now_add handles it
        }
    )

    if created:
        messages.success(request, "Thank you! Your rating has been submitted.")
    else:
        messages.success(request, "Your rating has been updated.")

    # Always reload the profile page with the rating-and-feedback partial
    return redirect('profile_section', section='rating-and-feedback')
    
@require_POST
@login_required
def update_emergency_contact(request):
    if request.method == "POST":
        form = EmergencyContactForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save(update_fields=["emergency_contact"])  # only update this field
            print(f"[DEBUG] Emergency contact updated to: {form.instance.emergency_contact}")
            context = {
                "form": EmergencyContactForm(instance=request.user),  # always return a form
                "success_message": "Emergency contact saved successfully!",
            }
        else:
            print("[DEBUG] Form errors:", form.errors)
            context = {"form": form}
    else:
        form = EmergencyContactForm(instance=request.user)
        context = {"form": form}

    return render(request, "passenger/partials/emergency_contact.html", context)

@login_required
def delete_passenger_account(request):
    user = request.user
    context = {}

    if request.method == 'POST':
        confirm_delete = request.POST.get('confirm_delete') == 'on'
        if confirm_delete:
            logout(request)
            user.delete()
            messages.success(request, "Your account has been deleted successfully.")
            return redirect('homepage')
        else:
            messages.error(request, "Please confirm account deletion by checking the box.")

    return render(request, 'passenger/partials/delete_account.html', context)

def faq_page(request):
    from django.db.models import Prefetch

    main_topics = MainTopic.objects.prefetch_related(
        Prefetch(
            'sub_topics',
            queryset=SubTopic.objects.prefetch_related(
                Prefetch(
                    'faqs',
                    queryset=FAQ.objects.all().order_by('question'),
                    to_attr='faq_list'
                )
            ),
            to_attr='subtopic_list'
        )
    ).order_by('name')

    return render(request, 'passenger/faq.html', {'main_topics': main_topics})


# Book Ride View
@login_required
def book_ride_view(request):
    pickup = request.GET.get('pickup') or request.session.get('pickup_location')
    dropoff = request.GET.get('dropoff') or request.session.get('dropoff_location')
    service = request.GET.get('service_name') or request.session.get('chosen_service')
    fare = request.GET.get('fare') or request.session.get('fare')
    ride_date = request.GET.get('ride_date')
    ride_time = request.GET.get('ride_time')
    ride_type = request.GET.get('ride_type')
    rental_duration = request.GET.get('rental_duration')
    pickup_city = request.GET.get('pickup_city')
    pickup_district = request.GET.get('pickup_district')
    pickup_state = request.GET.get('pickup_state')
    drop_city = request.GET.get('drop_city')
    drop_district = request.GET.get('drop_district')
    drop_state = request.GET.get('drop_state')
    distance_km = request.GET.get('distance_km')
    duration_min = request.GET.get('duration_min')
    distance_value = parse_decimal(distance_km)
    duration_value = parse_decimal(duration_min)
    if distance_value is None or distance_value <= 0 or duration_value is None or duration_value <= 0:
        messages.error(request, "Unable to verify route distance. Please select suggested locations and try again.")
        return redirect('choose_ride')
    pickup_meta = build_meta(pickup_city, pickup_district, pickup_state)
    drop_meta = build_meta(drop_city, drop_district, drop_state)
    derived = derive_ride_type(
        ride_type,
        pickup_meta,
        drop_meta,
        distance_value,
        threshold_km=get_outstation_threshold_km(),
    )
    ride_type = derived["ride_type"]

    # Store ride details in session
    request.session['pickup_location'] = pickup
    request.session['dropoff_location'] = dropoff
    request.session['chosen_service'] = service
    request.session['fare'] = fare
    request.session['ride_date'] = ride_date
    request.session['ride_time'] = ride_time
    request.session['ride_type'] = ride_type
    request.session['rental_duration'] = rental_duration
    request.session['pickup_city'] = pickup_city
    request.session['pickup_district'] = pickup_district
    request.session['pickup_state'] = pickup_state
    request.session['drop_city'] = drop_city
    request.session['drop_district'] = drop_district
    request.session['drop_state'] = drop_state
    request.session['distance_km'] = distance_km
    request.session['duration_min'] = duration_min

    context = {
        'pickup': pickup,
        'dropoff': dropoff,
        'selected_service': service,
        'fare': fare,
        'ride_date': ride_date,
        'ride_time': ride_time,
        'ride_type': ride_type,
        'rental_duration': rental_duration,
        'pickup_city': pickup_city,
        'pickup_district': pickup_district,
        'pickup_state': pickup_state,
        'drop_city': drop_city,
        'drop_district': drop_district,
        'drop_state': drop_state,
        'distance_km': distance_km,
        'duration_min': duration_min,
        'payment_modes': ['Cash', 'Credit Card', 'Debit Card', 'UPI', 'Wallet', 'Netbanking']
    }
    print(f"[DEBUG] Booking View - Pickup: {pickup}, Dropoff: {dropoff}, Service: {service}, Fare: {fare}")
    return render(request, 'passenger/book_ride.html', context)


@login_required
def confirm_booking(request):
    if request.method == 'POST':
        selected_vehicle_type = request.POST.get('vehicle_type')
        pickup_location = request.POST.get('pickup')
        dropoff_location = request.POST.get('dropoff')
        fare_str = request.POST.get('fare')
        ride_date_str = request.POST.get('ride_date')
        ride_time_str = request.POST.get('ride_time')
        ride_type = request.POST.get('ride_type')
        pickup_city = request.POST.get('pickup_city')
        pickup_district = request.POST.get('pickup_district')
        pickup_state = request.POST.get('pickup_state')
        drop_city = request.POST.get('drop_city')
        drop_district = request.POST.get('drop_district')
        drop_state = request.POST.get('drop_state')
        distance_km = request.POST.get('distance_km')
        duration_min = request.POST.get('duration_min')

        # ✅ Capture payment mode
        payment_mode = request.POST.get('payment_mode')
        rental_duration = request.POST.get('rental_duration')
        promo_code_input = request.POST.get('promo_code', '').strip()

        print(f"DEBUG: selected_vehicle_type received: '{selected_vehicle_type}', payment_mode: '{payment_mode}'")

        if not selected_vehicle_type:
            print("DEBUG: No vehicle type selected.")
            return render(request, 'passenger/ride_confirmed.html', {
                'error': 'No vehicle type selected.',
                'ride_type': ride_type
            })

        distance_value = parse_decimal(distance_km)
        duration_value = parse_decimal(duration_min)
        if distance_value is None or distance_value <= 0 or duration_value is None or duration_value <= 0:
            return render(request, 'passenger/ride_confirmed.html', {
                'error': 'Route distance could not be verified. Please go back and reselect pickup/dropoff from suggestions.',
                'ride_type': ride_type
            })
        pickup_meta = build_meta(pickup_city, pickup_district, pickup_state)
        drop_meta = build_meta(drop_city, drop_district, drop_state)
        derived = derive_ride_type(
            ride_type,
            pickup_meta,
            drop_meta,
            distance_value,
            threshold_km=get_outstation_threshold_km(),
        )
        derived_ride_type = derived["ride_type"]

        # Backend safeguard: prevent Daily rides for outstation trips
        if ride_type and ride_type.lower() == 'daily' and derived_ride_type == 'outstation':
            return render(request, 'passenger/ride_confirmed.html', {
                'error': 'Daily Ride is only available within the same city/service area. Please choose Outstation.',
                'ride_type': derived_ride_type
            })

        ride_type = derived_ride_type

        try:
            service_type_obj = ServiceType.objects.get(name__iexact=selected_vehicle_type)
        except ServiceType.DoesNotExist:
            print(f"DEBUG: ServiceType '{selected_vehicle_type}' not found in database.")
            return render(request, 'passenger/ride_confirmed.html', {
                'error': f"Selected service type '{selected_vehicle_type}' is invalid.",
                'ride_type': ride_type
            })

        if not is_vehicle_allowed(ride_type, service_type_obj.name):
            return render(request, 'passenger/ride_confirmed.html', {
                'error': f"{service_type_obj.name} is not available for Outstation rides.",
                'ride_type': ride_type
            })

        # Convert fare to Decimal
        try:
            fare = Decimal(fare_str.replace('₹', '').strip())
        except Exception as e:
            print(f"ERROR: Invalid fare value: {fare_str} ({e})")
            return render(request, 'passenger/ride_confirmed.html', {
                'error': 'Invalid fare value.',
                'ride_type': ride_type
            })

        # ===== Promo Code Validation & Application =====
        if promo_code_input:
            try:
                promo = PromoCode.objects.get(code__iexact=promo_code_input)
                from django.utils import timezone
                now = timezone.now()

                if promo.start_time and now < promo.start_time:
                    messages.error(request, "Promo code is not active yet.")
                elif promo.expiry_time and now > promo.expiry_time:
                    messages.error(request, "Promo code has expired.")
                elif promo.max_usage and promo.times_used >= promo.max_usage:
                    messages.error(request, "Promo code usage limit reached.")
                else:
                    discount = Decimal('0')
                    if promo.percentage_value:
                        discount = (fare * Decimal(promo.percentage_value) / Decimal('100'))
                        if promo.discount_amount:
                            discount = min(discount, Decimal(promo.discount_amount))
                    else:
                        discount = Decimal(promo.discount_amount)

                    fare = max(fare - discount, Decimal('0'))
                    promo.times_used += 1
                    promo.save()
                    messages.success(request, f"Promo applied! New fare: ₹{fare}")
                    print(f"[DEBUG] Promo '{promo.code}' applied. Discount: ₹{discount}, Final Fare: ₹{fare}")

            except PromoCode.DoesNotExist:
                messages.error(request, "Invalid promo code.")
            except Exception as e:
                print(f"ERROR applying promo code: {e}")
                messages.error(request, "Error applying promo code.")

        # ===== Find matching drivers =====
        matching_drivers = Driver.objects.filter(
            vehicle_type__iexact=selected_vehicle_type,
            availability=True,
            status='Active',
            is_deleted=False
        )

        if matching_drivers.exists():
            from django.utils import timezone
            booking_option = "now" if (not ride_date_str or not ride_time_str) else "later"
            if booking_option == "now":
                scheduled_time_value = timezone.now()
            else:
                scheduled_time_value = None
                if ride_date_str and ride_time_str:
                    try:
                        scheduled_time_value = timezone.datetime.strptime(
                            f"{ride_date_str} {ride_time_str}", "%Y-%m-%d %H:%M"
                        )
                        scheduled_time_value = timezone.make_aware(scheduled_time_value)
                    except ValueError:
                        print(f"DEBUG: Could not parse scheduled time: {ride_date_str} {ride_time_str}")
                if scheduled_time_value is None:
                    scheduled_time_value = timezone.now()

            try:
                pickup_latitude = Decimal('0.0')
                pickup_longitude = Decimal('0.0')
                drop_latitude = Decimal('0.0')
                drop_longitude = Decimal('0.0')

                # ✅ Include payment_mode in RideRequest for tracking
                ride_request = RideRequest.objects.create(
                    user=request.user,
                    pickup_location=pickup_location,
                    dropoff_location=dropoff_location,
                    pickup_latitude=pickup_latitude,
                    pickup_longitude=pickup_longitude,
                    drop_latitude=drop_latitude,
                    drop_longitude=drop_longitude,
                    fare=fare,
                    service_type=service_type_obj,
                    scheduled_time=scheduled_time_value,
                    status='Requested',
                    payment_mode=payment_mode 
                )
                print(f"[DEBUG] Ride request created with ID: {ride_request.id}, Payment Mode: {payment_mode}")

                # ===== Compute candidate driver queue: order by rating desc, shuffle ties =====
                # Group drivers by rating, shuffle within each rating, then flatten
                from collections import defaultdict
                import random

                rating_to_drivers = defaultdict(list)
                for d in matching_drivers:
                    rating_value = float(d.rating or 0.0)
                    rating_to_drivers[rating_value].append(d)

                ordered_ratings = sorted(rating_to_drivers.keys(), reverse=True)
                candidate_ids = []
                for r in ordered_ratings:
                    group = rating_to_drivers[r]
                    random.shuffle(group)
                    candidate_ids.extend([d.driver_id for d in group])

                # Persist queue in cache for 10 minutes
                queue_key = f"ride_request:{ride_request.id}:driver_queue"
                cache.set(queue_key, candidate_ids, timeout=60 * 10)

                # Assign the first available driver immediately (soft assignment)
                if candidate_ids:
                    first_driver_id = candidate_ids[0]
                    try:
                        assigned_driver = Driver.objects.get(driver_id=first_driver_id)
                        ride_request.driver = assigned_driver
                        ride_request.save(update_fields=['driver'])
                        print(f"[DEBUG] Initially assigned Driver {first_driver_id} to RideRequest {ride_request.id}")
                    except Driver.DoesNotExist:
                        pass

            except Exception as e:
                print(f"ERROR: Failed to create ride request: {e}")
                return render(request, 'passenger/ride_confirmed.html', {
                    'error': 'Failed to create ride request. Please try again.',
                    'ride_type': ride_type
                })

            return redirect('waiting_for_driver', ride_request_id=ride_request.id)

        else:
            context = {
                'no_driver': True,
                'vehicle_type': selected_vehicle_type,
                'ride_type': ride_type,
            }
            return render(request, 'passenger/ride_confirmed.html', context)

    return redirect('choose_ride')

@login_required
@require_POST
def reassign_next_driver(request, ride_request_id):
    """
    Reassign the ride request to the next available driver from the cached queue
    if the current assigned driver has not accepted within the allowed time.
    Simple, stateless trigger suitable for JS timer/polling.
    """
    try:
        ride_request = RideRequest.objects.select_related('booking', 'user', 'service_type').get(id=ride_request_id)
    except RideRequest.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Ride request not found'}, status=404)

    # Only the owner passenger can trigger reassignment
    if ride_request.user != request.user:
        return JsonResponse({'success': False, 'message': 'Not authorized'}, status=403)

    # If already accepted and booking created, do nothing
    if ride_request.status in ['Accepted', 'Rejected', 'Expired'] or getattr(ride_request, 'booking', None):
        return JsonResponse({'success': True, 'message': 'Ride already resolved'})

    queue_key = f"ride_request:{ride_request.id}:driver_queue"
    candidate_ids = cache.get(queue_key) or []

    # Remove current assignment from queue head if it matches
    if ride_request.driver_id and candidate_ids and candidate_ids[0] == ride_request.driver_id:
        candidate_ids = candidate_ids[1:]

    # Find the next available driver
    next_driver = None
    while candidate_ids:
        candidate_id = candidate_ids[0]
        try:
            d = Driver.objects.get(driver_id=candidate_id, availability=True, status='Active', is_deleted=False)
        except Driver.DoesNotExist:
            candidate_ids = candidate_ids[1:]
            continue
        next_driver = d
        break

    # Update cache with the remaining queue
    cache.set(queue_key, candidate_ids, timeout=60 * 10)

    if next_driver is None:
        # No more drivers available, mark as expired
        ride_request.status = 'Expired'
        ride_request.save(update_fields=['status'])
        return JsonResponse({'success': True, 'exhausted': True})

    # Soft-assign to next driver
    ride_request.driver = next_driver
    ride_request.save(update_fields=['driver'])
    return JsonResponse({'success': True, 'driver_id': next_driver.driver_id})

@login_required
def waiting_for_driver_view(request, ride_request_id):
    try:
        ride_request = RideRequest.objects.select_related('booking', 'service_type').get(id=ride_request_id)
    except RideRequest.DoesNotExist:
        return redirect('homepage')

    # Check user ownership directly from RideRequest.user
    if ride_request.user != request.user:
        return redirect('homepage')

    # Prefer booking if exists (driver may be assigned), else show ride_request details
    if ride_request.booking:
        pickup = ride_request.booking.pickup_location
        dropoff = ride_request.booking.dropoff_location
        fare = ride_request.booking.fare
        service_type_name = ride_request.booking.service_type.name
        ride_type = ride_request.booking.service_type.name
        scheduled_time = ride_request.booking.scheduled_time
    else:
        pickup = ride_request.pickup_location
        dropoff = ride_request.dropoff_location
        fare = ride_request.fare
        service_type_name = ride_request.service_type.name if ride_request.service_type else ""
        ride_type = ride_request.service_type.name if ride_request.service_type else ""
        scheduled_time = ride_request.scheduled_time

    return render(request, 'passenger/waiting_for_driver.html', {
        'ride_request_id': ride_request.id,
        'pickup': pickup,
        'dropoff': dropoff,
        'fare': fare,
        'scheduled_time': scheduled_time,
        'selected_service': service_type_name,
        'ride_type': ride_type,
    })


# Lightweight API for polling driver assignment by ride_request_id
@csrf_exempt
def check_driver_assignment(request, ride_request_id):
    try:
        rr = RideRequest.objects.select_related('booking').get(id=ride_request_id)
    except RideRequest.DoesNotExist:
        return JsonResponse({'driver_assigned': False})

    # If a Booking exists, navigate to confirmation regardless of Booking.status
    if getattr(rr, 'booking', None):
        booking = rr.booking
        if booking and booking.driver:
            driver = booking.driver
            driver_name = f"{driver.first_name} {driver.last_name}" if driver.first_name and driver.last_name else driver.name
            driver_phone = getattr(driver, 'phone', "N/A")
            vehicle_info = f"{getattr(driver, 'vehicle_type', 'Unknown')} - {getattr(driver, 'vehicle_number', 'N/A')}"
            return JsonResponse({
                'driver_assigned': True,
                'driver_name': driver_name,
                'driver_phone': driver_phone,
                'vehicle_info': vehicle_info,
                'booking_id': booking.booking_id
            })
        # Booking exists but no driver? treat as not yet
        return JsonResponse({'driver_assigned': False})

    # Fallback: no booking yet
    return JsonResponse({'driver_assigned': False})


@login_required
@require_POST
def cancel_booking(request):
    booking_id = request.POST.get('booking_id')
    print(f"DEBUG: Attempting to cancel booking ID: {booking_id}")
    try:
        # Ensure the booking belongs to the current user
        booking = Booking.objects.get(booking_id=booking_id, user=request.user)
        booking.status = 'Cancelled'
        booking.driver = None  # Unassign driver from the cancelled booking
        booking.save()

        # Invalidate ride PIN if present
        ride_pin = getattr(booking, 'ride_pin', None)
        if ride_pin:
            ride_pin.is_active = False
            ride_pin.pin_plain = ''
            ride_pin.save(update_fields=['is_active', 'pin_plain'])

        messages.success(request, f"Booking #{booking_id} has been cancelled.")
        print(f"DEBUG: Booking #{booking_id} cancelled successfully.")
    except Booking.DoesNotExist:
        messages.error(request, "Booking not found or you don't have permission to cancel it.")
        print(f"ERROR: Booking #{booking_id} not found for user {request.user.id} or permission denied.")
    except Exception as e:
        messages.error(request, f"An error occurred while cancelling booking: {e}")
        print(f"ERROR: Exception during cancellation of booking #{booking_id}: {e}")

    return redirect('homepage') 

def booking_confirmed_view(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)

    ride_pin_obj = RidePin.objects.filter(booking=booking).first()
    if not ride_pin_obj:
        from django.contrib.auth.hashers import make_password
        import random
        pin_value = f"{random.randint(0, 9999):04d}"
        ride_pin_obj = RidePin.objects.create(
            booking=booking,
            pin_hash=make_password(pin_value),
            pin_plain=pin_value,
            attempts=0,
            locked_until=None,
            is_active=True,
            is_verified=False,
        )


    context = {
        'booking': booking,
        'booking_id': booking.booking_id,
        'pickup': booking.pickup_location,
        'dropoff': booking.dropoff_location,
        'fare': booking.fare,
        'selected_service': booking.service_type.name,
        'driver': booking.driver,
        'eta_message': "Your driver will arrive in 5-10 minutes",
        'ride_pin': ride_pin_obj.pin_plain if ride_pin_obj and ride_pin_obj.is_active else None,
    }

    return render(request, 'passenger/ride_confirmed.html', context)

@login_required
def check_ride_status(request, ride_request_id):
    try:
        ride_request = RideRequest.objects.select_related('booking').get(id=ride_request_id)
    except RideRequest.DoesNotExist:
        return JsonResponse({'status': 'Not Found'})

    # Treat existence of a Booking as the signal to move passenger forward
    if getattr(ride_request, 'booking', None):
        return JsonResponse({'status': 'Confirmed', 'booking_id': ride_request.booking.booking_id})

    if ride_request.status in ["Rejected", "Expired", "Cancelled"]:
        return JsonResponse({'status': ride_request.status})
    return JsonResponse({'status': 'Requested'})

def booking_confirmed_view(request, booking_id):
    # This view now needs to get the Booking object instead of a RideRequest
    # as the waiting page will redirect here with a booking_id.
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)

    # Fetch or fallback-create ride PIN (should be created when driver accepted)
    ride_pin_obj = RidePin.objects.filter(booking=booking).first()
    if not ride_pin_obj:
        # Safety net: generate if missing
        from django.contrib.auth.hashers import make_password
        import random
        pin_value = f"{random.randint(0, 9999):04d}"
        ride_pin_obj = RidePin.objects.create(
            booking=booking,
            pin_hash=make_password(pin_value),
            pin_plain=pin_value,
            attempts=0,
            locked_until=None,
            is_active=True,
            is_verified=False,
        )

    driver_vehicle = {}
    if booking.driver:
        driver_vehicle = {
            'model': booking.driver.manufacturer or booking.driver.vehicle_type or '',
            'color': booking.driver.color or '',
            'plate': booking.driver.plate_number or '',
        }
        driver_phone = booking.driver.phone if hasattr(booking.driver, "phone") else ""
    else:
        driver_phone = ""

    context = {
        'booking': booking,
        'booking_id': booking.booking_id,
        'pickup': booking.pickup_location,
        'dropoff': booking.dropoff_location,
        'fare': booking.fare,
        'selected_service': booking.service_type.name,
        'driver': booking.driver,
        'driver_phone': driver_phone,
        'eta_message': "Your driver will arrive in 5-10 minutes",
        'ride_pin': ride_pin_obj.pin_plain if ride_pin_obj and ride_pin_obj.is_active else None,
        'driver_vehicle': driver_vehicle,
    }
    return render(request, 'passenger/ride_confirmed.html', context)

def apply_promo_code(fare, promo_code, user):
    """
    Apply a promo code to a fare using your PromoCode model.
    Uses:
      - type: 'Flat' or 'Percent'
      - percentage_value: percentage for 'Percent' type
      - discount_amount: 
          * Flat: exact amount to subtract
          * Percent: max cap for the calculated percentage discount
      - start_time / expiry_time: validity dates
      - max_usage / max_usage_per_user: usage limits
    """
    code = (promo_code or "").strip()
    if not code:
        return fare, None

    try:
        promo = PromoCode.objects.get(code__iexact=code)
    except PromoCode.DoesNotExist:
        return fare, "Invalid promo code."

    now = timezone.now()

    # Validity window
    if promo.start_time and now < promo.start_time:
        return fare, "Promo code not active yet."
    if promo.expiry_time and now > promo.expiry_time:
        return fare, "Promo code has expired."

    # Optional: enforce usage limits if you have a usage log model
    PromoCodeUsage = None
    try:
        from promo.models import PromoCodeUsage
    except ImportError:
        pass

    if PromoCodeUsage and promo.max_usage is not None:
        total_uses = PromoCodeUsage.objects.filter(promo=promo).count()
        if total_uses >= promo.max_usage:
            return fare, "Promo code usage limit reached."

    if PromoCodeUsage and promo.max_usage_per_user is not None:
        user_uses = PromoCodeUsage.objects.filter(promo=promo, user=user).count()
        if user_uses >= promo.max_usage_per_user:
            return fare, "You have already used this promo code the maximum number of times."

    # Calculate discount
    discount = Decimal('0.00')
    promo_type = (promo.type or "").lower()

    if promo_type == 'flat':
        discount = Decimal(promo.discount_amount or 0)

    elif promo_type == 'percent':
        percentage = Decimal(promo.percentage_value or 0)
        raw_discount = (Decimal(fare) * percentage / Decimal('100')).quantize(Decimal('0.01'))
        cap = Decimal(promo.discount_amount or 0)
        discount = min(raw_discount, cap) if cap > 0 else raw_discount

    else:
        return fare, "Invalid promo type."

    final_fare = Decimal(fare) - discount
    if final_fare < 0:
        final_fare = Decimal('0.00')

    if PromoCodeUsage and discount > 0:
        PromoCodeUsage.objects.create(promo=promo, user=user, discount_applied=discount)

    return final_fare, None


# New API view for applying promo code via AJAX/JSON
@login_required
@require_POST
def apply_promo(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        promo_code = data.get('promo_code')
        fare = data.get('fare')
        if promo_code is None or fare is None:
            return JsonResponse({'success': False, 'message': 'Both promo_code and fare are required.'}, status=400)

        discounted_fare, message = apply_promo_code(fare, promo_code, request.user)
        if message is not None:
            return JsonResponse({'success': False, 'message': message})
        return JsonResponse({
            'success': True,
            'discounted_fare': str(discounted_fare),
            'message': "Promo code applied successfully."
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

def ride_started_view(request, booking_id):
    """
    Passenger-facing view to display ride started details.
    """
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)

    # If the ride is already completed, send the passenger to the completed page
    if booking.status == 'Completed':
        return redirect('ride_completed', booking_id=booking.booking_id)

    driver_vehicle = {}
    if booking.driver:
        driver_vehicle = {
            'model': booking.driver.manufacturer or booking.driver.vehicle_type or '',
            'color': booking.driver.color or '',
            'plate': booking.driver.plate_number or '',
            'name': f"{booking.driver.first_name or ''} {booking.driver.last_name or ''}".strip() or (booking.driver.email or "Driver"),
        }

    support_phone = getattr(settings, "SUPPORT_PHONE", "") if 'settings' in globals() else ""
    tracking_url = request.build_absolute_uri(reverse("ride_started", args=[booking.booking_id]))

    # Show the current time as the ride's start time (since Booking has no explicit start_time field yet).
    context = {
        "booking": booking,
        "start_time": timezone.localtime(timezone.now()).strftime("%d %b %Y, %I:%M %p"),
        "driver_vehicle": driver_vehicle,
        "tracking_url": tracking_url,
        "support_phone": support_phone,
    }
    return render(request, "passenger/ride_started.html", context)

def booking_status_api(request, booking_id):
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        arrived = cache.get(f"booking:{booking_id}:arrived", False)
        return JsonResponse({"status": booking.status, "arrived": bool(arrived)})
    except Booking.DoesNotExist:
        return JsonResponse({"status": "not_found"})

@login_required
def booking_details_api(request, booking_id):
    """
    API endpoint to fetch booking details for the unified dashboard.
    """
    try:
        booking = Booking.objects.select_related('driver', 'service_type', 'user').get(
            booking_id=booking_id,
            user=request.user
        )
        
        driver_data = None
        if booking.driver:
            driver_data = {
                'first_name': booking.driver.first_name or '',
                'last_name': booking.driver.last_name or '',
                'vehicle_type': booking.driver.vehicle_type or '',
                'vehicle_number': booking.driver.vehicle_number or '',
                'phone': getattr(booking.driver, 'phone', 'N/A'),
            }
        
        return JsonResponse({
            'success': True,
            'booking_id': booking.booking_id,
            'status': booking.status,
            'pickup': booking.pickup_location,
            'dropoff': booking.dropoff_location,
            'fare': str(booking.fare),
            'service_type': booking.service_type.name if booking.service_type else '',
            'driver': driver_data,
            'scheduled_time': booking.scheduled_time.isoformat() if booking.scheduled_time else None,
        })
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def driver_arrived_view(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    ride_pin_obj = RidePin.objects.filter(booking=booking, is_active=True).first()
    context = {
        'booking': booking,
        'driver': booking.driver,
        'ride_pin': ride_pin_obj.pin_plain if ride_pin_obj else None,
    }
    return render(request, 'passenger/driver_arrived.html', context)

@login_required
def ride_completed_view(request, booking_id):
    """
    Passenger-facing view to display ride completed details with total fare.
    """
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    if booking.status != 'Completed':
        # Optionally guard against early access; redirect to appropriate page
        return redirect('ride_started', booking_id=booking.booking_id)

    context = {
        'booking': booking,
    }
    return render(request, 'passenger/ride_completed.html', context)
