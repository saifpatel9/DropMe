from django.shortcuts import render, get_object_or_404, redirect
from passenger.models import User
from wallet.models import Wallet, WalletPayment
from .forms import PassengerForm
from driver.models import Driver
from booking.models import Booking
from vehicle.models import Vehicle
from services.models import ServiceType, FareSlab
from services.forms import ServiceTypeForm, FareSlabForm
from promo.models import PromoCode
from django.utils.timezone import now
from django.contrib import messages
from .forms import DriverForm
from vehicle.forms import VehicleForm 
from rating.models import Rating
from faq.models import FAQ, MainTopic, SubTopic
from django.db.models import Count, Q, Avg
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from .utils import admin_login_required
from feedback.models import Feedback
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from payments.models import Payment
from django.utils import timezone
import datetime

@admin_login_required
def adminpanel_dashboard(request):
    total_users = User.objects.count()
    total_drivers = Driver.objects.count()
    total_bookings = Booking.objects.count()

    # Revenue metrics
    today = timezone.now().date()
    completed_payments = Payment.objects.filter(status='completed')
    total_revenue = completed_payments.aggregate(total=Sum('amount'))['total'] or 0
    todays_revenue = completed_payments.filter(paid_at__date=today).aggregate(total=Sum('amount'))['total'] or 0

    # Today's bookings (based on scheduled_time date if available)
    todays_bookings = Booking.objects.filter(scheduled_time__date=today).count()

    context = {
        'total_users': total_users,
        'total_drivers': total_drivers,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'todays_revenue': todays_revenue,
        'todays_bookings': todays_bookings,
    }

    return render(request, 'adminpanel/dashboard.html', context)
from django.contrib.auth.hashers import check_password
from .models import AdminUser

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = AdminUser.objects.get(email=email)
            if check_password(password, user.password):
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f"Welcome back, {user.email}!")
                return redirect('adminpanel_dashboard')
            else:
                messages.error(request, "Invalid password.")
        except AdminUser.DoesNotExist:
            messages.error(request, "Invalid email.")
    
    return render(request, 'adminpanel/admin_login.html')


@admin_login_required
def admin_passengers(request):
    passengers = User.objects.all()
    return render(request, 'adminpanel/passengers.html', {'passengers': passengers})

@admin_login_required
def view_passenger(request, user_id):
    passenger = get_object_or_404(User, user_id=user_id)
    rides = Booking.objects.filter(user_id=passenger.user_id).order_by('-scheduled_time')

    return render(request, 'adminpanel/view_passenger.html', {
        'passenger': passenger,
        'rides': rides,
    })

@admin_login_required
def edit_passenger(request, user_id):
    user = get_object_or_404(User, user_id=user_id)

    if request.method == 'POST':
        form = PassengerForm(request.POST, instance=user)
        if form.is_valid():
            passenger = form.save(commit=False)
            passenger.payment_method = request.POST.get('payment_method')
            passenger.status = request.POST.get('status', 'Inactive')
            passenger.is_verified = request.POST.get('is_verified') == 'True'
            passenger.save()
            return redirect('admin_passengers')
    else:
        form = PassengerForm(instance=user)

    return render(request, 'adminpanel/edit_passenger.html', {'form': form, 'user': user})

@admin_login_required
def delete_passenger(request, user_id):
    user = get_object_or_404(User, user_id=user_id)

    if request.method == "POST":
        user.delete()
        messages.success(request, "Passenger deleted successfully.")
        return redirect('admin_passengers')  # your listing page

    # Optional: Prevent GET-based delete flow
    messages.warning(request, "Invalid request method.")
    return redirect('admin_passengers')

@admin_login_required
def decline_passenger(request, user_id):
    user = get_object_or_404(User, user_id=user_id)
    user.status = 'Inactive'
    user.save()
    messages.warning(request, f"Passenger {user.first_name} {user.last_name} has been declined.")
    return redirect('admin_passengers')

@admin_login_required
def admin_drivers(request):
    drivers = Driver.objects.filter(is_deleted=False).annotate(
        total_rides=Count('booking', distinct=True),
        completed_rides=Count('booking', filter=Q(booking__status='Completed'), distinct=True),
        average_rating=Avg('driver_ratings__rating', filter=Q(driver_ratings__given_by='user'))
    )
    return render(request, 'adminpanel/drivers.html', {'drivers': drivers})

@admin_login_required
def add_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST, request.FILES)
        if form.is_valid():
            driver = form.save(commit=False) 
            if driver.password_hash:
                driver.password_hash = make_password(driver.password_hash)
            if not driver.rating:
                driver.rating = 0.00 
            if not driver.created_at:
                driver.created_at = timezone.now()
            driver.save()
            messages.success(request, 'Driver added successfully!') 
            return redirect('admin_drivers') 
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DriverForm()
    context = {'form': form}
    return render(request, 'adminpanel/add_driver.html', context)

@admin_login_required
def view_driver(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)
    
    
    average_rating_data = Rating.objects.filter(
        driver=driver, 
        given_by='user'
    ).aggregate(avg_rating=Avg('rating')) 
    driver_average_rating = average_rating_data['avg_rating']

    return render(request, 'adminpanel/view_driver.html', {
        'driver': driver,
        'driver_average_rating': driver_average_rating
    })

@admin_login_required
def edit_driver(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)

    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, "Driver details updated successfully.")
            return redirect('admin_drivers')
    else:
        form = DriverForm(instance=driver)
        print("Form is NOT valid. Errors:", form.errors)

    return render(request, 'adminpanel/edit_driver.html', {'form': form, 'driver': driver})

@admin_login_required
def decline_driver(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)
    driver.status = 'Inactive'
    driver.save()
    messages.warning(request, f"Driver {driver.first_name} {driver.last_name} has been declined.")
    return redirect('admin_drivers')

@admin_login_required
def delete_driver(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)

    if request.method == 'POST':
        driver.is_deleted = True
        driver.save()
        messages.success(request, "Driver marked as deleted.")
        return redirect('admin_drivers')

    messages.warning(request, "Invalid request method.")
    return redirect('admin_drivers')

@admin_login_required
def view_driver_history(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)
    rides = Booking.objects.filter(driver_id=driver.driver_id).order_by('-scheduled_time')

    return render(request, 'adminpanel/view_driver_history.html', {
        'driver': driver,
        'rides': rides
    })

@admin_login_required
def view_driver_documents(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)
    return render(request, 'adminpanel/view_driver_documents.html', {'driver': driver})

@admin_login_required
@require_POST
def update_driver_document_status(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)
    doc_type = request.POST.get("document_type")
    new_status = request.POST.get("new_status")

    # Map document_type to model field
    field_map = {
        "license_document": "license_document_status",
        "id_proof": "id_proof_status",
        "vehicle_rc": "vehicle_rc_status",
    }

    if doc_type not in field_map or new_status not in ["Pending", "Verified", "Rejected"]:
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    setattr(driver, field_map[doc_type], new_status)
    driver.save(update_fields=[field_map[doc_type]])

    return JsonResponse({"success": True, "status": new_status, "document_type": doc_type})

@admin_login_required
def admin_bookings(request):
    daily_type = ServiceType.objects.filter(name__iexact='Daily').first()
    rental_type = ServiceType.objects.filter(name__iexact='Rental').first()
    outstation_type = ServiceType.objects.filter(name__iexact='Outstation').first()

    total_requests = Booking.objects.count()
    ongoing_requests = Booking.objects.filter(status='Ongoing').count()
    completed_requests = Booking.objects.filter(status='Completed').count()
    cancelled_requests = Booking.objects.filter(status='Cancelled').count()

    daily_rides = Booking.objects.filter(service_type__name__iexact='Daily').count()
    rental_rides = Booking.objects.filter(service_type__name__iexact='Rental').count()
    outstation_rides = Booking.objects.filter(service_type__name__iexact='Outstation').count()
    scheduled_rides = Booking.objects.filter(scheduled_time__isnull=False).count()

    return render(request, 'adminpanel/booking.html', {
        'total_requests': total_requests,
        'ongoing_requests': ongoing_requests,
        'completed_requests': completed_requests,
        'cancelled_requests': cancelled_requests,
        'daily_rides': daily_rides,
        'rental_rides': rental_rides,
        'outstation_rides': outstation_rides,
        'scheduled_rides': scheduled_rides,
    })

@admin_login_required
def vehicle_dashboard(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'adminpanel/vehicle_dashboard.html', {'vehicles': vehicles})

@admin_login_required
def add_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle added successfully.")
            return redirect('vehicle_dashboard')
    else:
        form = VehicleForm()
    return render(request, 'adminpanel/add_vehicle.html', {'form': form})
@admin_login_required
def edit_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle details updated.")
            return redirect('vehicle_dashboard')
    else:
        form = VehicleForm(instance=vehicle)

    return render(request, 'adminpanel/edit_vehicle.html', {
        'form': form,
        'vehicle': vehicle
    })

@admin_login_required
def delete_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
    if request.method == 'POST':
        vehicle.delete()
        messages.warning(request, "Vehicle deleted.")
        return redirect('vehicle_dashboard')
    return render(request, 'adminpanel/confirm_delete_vehicle.html', {'vehicle': vehicle})

@admin_login_required
def view_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
    return render(request, 'adminpanel/view_vehicle.html', {'vehicle': vehicle})

@admin_login_required

def service_dashboard(request):
    services = ServiceType.objects.prefetch_related('fare_slabs').all()
    slabs = FareSlab.objects.select_related('service_type').all()
    
    context = {
        'services': services,
        'slabs': slabs
    }
    return render(request, 'adminpanel/service_dashboard.html', context)

@admin_login_required
def add_service(request):
    if request.method == 'POST':
        form = ServiceTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service added successfully.")
            return redirect('service_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceTypeForm()
    return render(request, 'adminpanel/add_service.html', {'form': form})

@admin_login_required
def edit_service(request, service_id):
    service = get_object_or_404(ServiceType, service_id=service_id)

    if request.method == 'POST':
        form = ServiceTypeForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated successfully.")
            return redirect('service_dashboard')
    else:
        form = ServiceTypeForm(instance=service)

    return render(request, 'adminpanel/edit_service.html', {'form': form, 'service': service})

@admin_login_required
def view_service(request, service_id):
    service = get_object_or_404(ServiceType, service_id=service_id)
    return render(request, 'adminpanel/view_service.html', {'service': service})

@admin_login_required
def delete_service(request, service_id):
    service = get_object_or_404(ServiceType, service_id=service_id)
    if request.method == 'POST':
        service.delete()
        messages.warning(request, "Service deleted successfully.")
        return redirect('service_dashboard')

    return render(request, 'adminpanel/confirm_delete_service.html', {'service': service})

@admin_login_required
def decline_service(request, service_id):
    service = get_object_or_404(ServiceType, service_id=service_id)
    service.status = 'Inactive'
    service.save()
    messages.warning(request, f"Service {service.name} has been declined.")
    return redirect('service_dashboard')

@admin_login_required
def add_promo(request):
    return render(request, 'adminpanel/add_promo.html')

@admin_login_required
def promo_dashboard(request):
    promos = PromoCode.objects.all()
    return render(request, 'adminpanel/promo_dashboard.html', {'promos': promos, 'now': now()})

@admin_login_required
def wallet_dashboard(request):
    wallets = Wallet.objects.select_related('user').all()
    wallet_payments = WalletPayment.objects.select_related('user').all() 
    return render(request, 'adminpanel/wallet_dashboard.html', {
        'wallets': wallets,
        'wallet_payments': wallet_payments
    })

@admin_login_required
def wallet_transactions(request, wallet_id):
    wallet = get_object_or_404(Wallet, wallet_id=wallet_id)
    transactions = WalletPayment.objects.filter(wallet=wallet).order_by('-paid_at')
    return render(request, 'adminpanel/wallet_transactions.html', {
        'wallet': wallet,
        'transactions': transactions
    })

@admin_login_required
def wallet_redeems(request, wallet_id):
    wallet = get_object_or_404(Wallet, pk=wallet_id)
    # Filter by title or logic that identifies redeems
    redeems = WalletPayment.objects.filter(wallet=wallet, title__icontains="redeem")
    return render(request, "adminpanel/wallet_redeem.html", {
        "wallet": wallet,
        "redeems": redeems
    })

@admin_login_required
def view_wallet_payment(request, wallet_payment_id):
    payment = get_object_or_404(WalletPayment, wallet_payment_id=wallet_payment_id)
    return render(request, 'adminpanel/view_wallet_payments.html', {'payment': payment})

@admin_login_required
def rating_dashboard(request):
    # Ratings where the passenger (User) rated the driver
    user_ratings = Rating.objects.select_related('User', 'driver', 'booking') \
                                 .filter(given_by='user')

    # Ratings where the driver rated the passenger (User)
    driver_ratings = Rating.objects.select_related('driver', 'User', 'booking') \
                                   .filter(given_by='driver')

    context = {
        'user_ratings': user_ratings,
        'driver_ratings': driver_ratings,
    }
    return render(request, 'adminpanel/rating_dashboard.html', context)


@admin_login_required
def passenger_rating_view(request):
    """View to show all passenger ratings (list view)"""
    passenger_ratings = Rating.objects.select_related('User', 'driver', 'booking') \
                                      .filter(given_by='user')
    return render(request, 'adminpanel/passenger_ratings_list.html', {
        'passenger_ratings': passenger_ratings
    })


@admin_login_required
def passenger_rating_detail(request, pk):
    passenger_rating = get_object_or_404(
        Rating.objects.select_related('User', 'driver', 'booking'),
        pk=pk,
        given_by='user'
    )
    return render(request, 'adminpanel/passenger_rating.html', {'rating': passenger_rating})


@admin_login_required
def driver_rating_view(request):
    driver_ratings = Rating.objects.select_related('driver', 'User', 'booking') \
                                   .filter(given_by='driver')
    return render(request, 'adminpanel/driver_ratings_list.html', {
        'driver_ratings': driver_ratings
    })


@admin_login_required
def driver_rating_detail(request, pk):
    rating = get_object_or_404(
        Rating.objects.select_related('driver', 'User', 'booking'),
        pk=pk,
        given_by='driver'
    )
    return render(request, 'adminpanel/driver_rating.html', {'rating': rating})

@admin_login_required
def faq_dashboard(request):
    faqs = FAQ.objects.select_related('main_topic', 'sub_topic').all()
    return render(request, 'faq/faq_dashboard.html', {'faqs': faqs})

@admin_login_required
def add_faq(request):
    if request.method == 'POST':
        main_topic_name = request.POST.get('main_topic_name')
        sub_topic_name = request.POST.get('sub_topic_name')
        question = request.POST.get('question')
        answer = request.POST.get('answer')

      
        main_topic, _ = MainTopic.objects.get_or_create(name=main_topic_name)

        sub_topic, _ = SubTopic.objects.get_or_create(name=sub_topic_name, main_topic=main_topic)

        FAQ.objects.create(
            main_topic=main_topic,
            sub_topic=sub_topic,
            question=question,
            answer=answer
        )
        return redirect('faq_dashboard')

    return render(request, 'faq/add_faq.html')

@admin_login_required
def edit_faq(request, faq_id):
    faq = get_object_or_404(FAQ, pk=faq_id)

    if request.method == 'POST':
        main_topic_name = request.POST.get('main_topic_name')
        sub_topic_name = request.POST.get('sub_topic_name')
        question = request.POST.get('question')
        answer = request.POST.get('answer')

        if not all([main_topic_name, sub_topic_name, question, answer]):
            return render(request, 'faq/edit_faq.html', {
                'faq': faq,
                'error': 'All fields are required.'
            })

        main_topic, _ = MainTopic.objects.get_or_create(name=main_topic_name)
        sub_topic, _ = SubTopic.objects.get_or_create(name=sub_topic_name, main_topic=main_topic)

        faq.main_topic = main_topic
        faq.sub_topic = sub_topic
        faq.question = question
        faq.answer = answer
        faq.save()

        return redirect('faq_dashboard')

    return render(request, 'faq/edit_faq.html', {'faq': faq})

@admin_login_required
def delete_faq(request, faq_id):
    faq = get_object_or_404(FAQ, pk=faq_id)
    if request.method == 'POST':
        faq.delete()
        return redirect('faq_dashboard')
    return render(request, 'faq/confirm_delete.html', {'faq': faq})

@admin_login_required
def faq_detail(request, faq_id):
    faq = get_object_or_404(FAQ, pk=faq_id)
    return render(request, 'faq/faq_detail.html', {'faq': faq})

# Payment Dashboard
@admin_login_required
def payment_dashboard(request):
    today = timezone.now().date()

    # === Completed payments queryset with service_type relation ===
    completed_payments = Payment.objects.filter(status="completed").select_related("booking__service_type")

    # === KPIs ===
    total_revenue = completed_payments.aggregate(total=Sum("amount"))["total"] or 0
    completed_count = completed_payments.count()
    pending_count = Payment.objects.filter(status="pending").count()
    failed_count = Payment.objects.filter(status="failed").count()
    refunded_count = Payment.objects.filter(status="refunded").count()

    # === Admin & Provider Earnings (dynamic commission) ===
    payments_with_commission = completed_payments.annotate(
        admin_earning=ExpressionWrapper(
            F("amount") * F("booking__service_type__admin_commission") / 100,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
        provider_earning=ExpressionWrapper(
            F("amount") * F("booking__service_type__provider_commission") / 100,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
    )

    total_profit = payments_with_commission.aggregate(total=Sum("admin_earning"))["total"] or 0
    total_provider_earning = payments_with_commission.aggregate(total=Sum("provider_earning"))["total"] or 0

    # === Payment Status Distribution ===
    payment_status_qs = Payment.objects.values("status").annotate(total=Count("payment_id"))
    payment_status_data = [
        {"status": item["status"], "total": item["total"]}
        for item in payment_status_qs
    ]

    # === Payment Modes ===
    payment_mode_qs = Payment.objects.values("payment_mode").annotate(total=Count("payment_id"))
    payment_mode_data = [
        {"payment_mode": item["payment_mode"], "total": item["total"]}
        for item in payment_mode_qs
    ]

    # === Revenue Trend (last 30 days) ===
    try:
        start_date = timezone.now() - datetime.timedelta(days=30)

        revenue_trend_qs = (
            Payment.objects.filter(status="completed", paid_at__isnull=False, paid_at__gte=start_date)
            .values("paid_at", "amount")
        )

        revenue_map = {}
        for p in revenue_trend_qs:
            date_str = p["paid_at"].date().strftime("%Y-%m-%d")
            revenue_map[date_str] = revenue_map.get(date_str, 0) + float(p["amount"] or 0)

        revenue_trend = [{"date": d, "total": t} for d, t in sorted(revenue_map.items())]

        if not revenue_trend:
            print("DEBUG - Revenue trend error: No revenue trend data")
        else:
            print("DEBUG - Revenue trend data:", revenue_trend)

    except Exception as e:
        print(f"DEBUG - Revenue trend error: {e}")
        revenue_trend = []


    # === Context ===
    context = {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_provider_earning": total_provider_earning,
        "completed_count": completed_count,
        "pending_count": pending_count,
        "failed_count": failed_count,
        "refunded_count": refunded_count,
        "payment_status_data": payment_status_data,
        "payment_mode_data": payment_mode_data,
        "revenue_trend": revenue_trend,
    }

    return render(request, "adminpanel/payment_dashboard.html", context)

@admin_login_required
def view_payment(request, payment_id):
    payment = get_object_or_404(Payment, payment_id=payment_id)

    passenger_name = "N/A"
    driver_name = "N/A"
    booking_id_display = "N/A"

    if payment.user:
        p_first_name = payment.user.first_name if hasattr(payment.user, 'first_name') else ''
        p_last_name = payment.user.last_name if hasattr(payment.user, 'last_name') else ''
        
        if p_first_name or p_last_name:
            passenger_name = f"{p_first_name} {p_last_name}".strip()
        elif hasattr(payment.user, 'username') and payment.user.username:
            passenger_name = payment.user.username
    elif payment.booking and payment.booking.user: # Fallback: get user from booking if payment.user is null
        b_user = payment.booking.user
        p_first_name = b_user.first_name if hasattr(b_user, 'first_name') else ''
        p_last_name = b_user.last_name if hasattr(b_user, 'last_name') else ''
        if p_first_name or p_last_name:
            passenger_name = f"{p_first_name} {p_last_name}".strip()
        elif hasattr(b_user, 'username') and b_user.username:
            passenger_name = b_user.username

    if payment.booking and payment.booking.driver:
        driver_obj = payment.booking.driver
        d_first_name = driver_obj.first_name if hasattr(driver_obj, 'first_name') else ''
        d_last_name = driver_obj.last_name if hasattr(driver_obj, 'last_name') else ''
        
        if d_first_name or d_last_name:
            driver_name = f"{d_first_name} {d_last_name}".strip()
        elif hasattr(driver_obj, 'name') and driver_obj.name:
            driver_name = driver_obj.name

    if payment.booking:
        booking_id_display = payment.booking.booking_id

    context = {
        'payment': payment,
        'passenger_name': passenger_name,
        'driver_name': driver_name,
        'booking_id_display': booking_id_display,
    }
    return render(request, 'adminpanel/view_payment.html', context)

@admin_login_required
def refund_payment(request, payment_id):
    payment = get_object_or_404(Payment, payment_id=payment_id)
    
    if request.method == 'POST':
        refund_reason = request.POST.get('refund_reason', '')
        
        payment.status = 'refunded'
       
        payment.save()
        messages.success(request, f'Payment {payment.payment_id} has been refunded successfully!')
        return redirect('payment_dashboard')
    
    messages.error(request, "Invalid access to refund page.")
    return redirect('payment_dashboard')

@admin_login_required
def feedback_dashboard(request):
    feedback_list = Feedback.objects.select_related('user').all()
    return render(request, 'adminpanel/feedback_dashboard.html', {
        'feedback_list': feedback_list
    })

#def edit_feedback(request, feedback_id):
#    feedback = get_object_or_404(Feedback, pk=feedback_id)
#    if request.method == 'POST':
#        feedback.message = request.POST.get('message')
#        feedback.stars = request.POST.get('stars')
#        feedback.save()
#        return redirect('feedback_dashboard')
#    return render(request, 'adminpanel/edit_feedback.html', {'feedback': feedback})

#def delete_feedback(request, feedback_id):
#    feedback = get_object_or_404(Feedback, pk=feedback_id)
#    feedback.delete()
#    return redirect('adminpanel/feedback_dashboard')

# Add FareSlab view for adminpanel
@admin_login_required
def add_fareslab(request):
    if request.method == 'POST':
        form = FareSlabForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fare slab added successfully.")
            return redirect('service_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FareSlabForm()
    return render(request, 'adminpanel/add_fareslab.html', {'form': form})

@login_required
def edit_fareslab(request, slab_id):
    slab = get_object_or_404(FareSlab, pk=slab_id)

    if request.method == 'POST':
        form = FareSlabForm(request.POST, instance=slab)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fare slab updated successfully.')
            return redirect('service_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FareSlabForm(instance=slab)

    return render(request, 'adminpanel/edit_fareslab.html', {'form': form, 'slab': slab})