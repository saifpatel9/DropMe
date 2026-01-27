from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from passenger.models import User
from driver.models import Driver


def unified_login_view(request):
    """
    Unified login for passenger/admin (Django auth) and driver (custom model).
    Redirects based on role:
      - Admin / staff / is_admin → admin panel dashboard
      - Authenticated passenger   → passenger homepage
      - Driver                    → driver homepage
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Try authenticating as Passenger/Admin user
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)

            # Admin / staff / superuser or explicit is_admin flag → admin panel
            if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False) or getattr(user, 'is_admin', False):
                return redirect('adminpanel_dashboard')

            # Default: treat as passenger
            return redirect('homepage')

        # Try authenticating as Driver
        try:
            driver = Driver.objects.get(email=email)
            if check_password(password, driver.password_hash):
                request.session['driver_id'] = driver.driver_id
                return redirect('driver_homepage')
        except Driver.DoesNotExist:
            pass

        messages.error(request, "Invalid email or password.")

    return render(request, 'passenger/login.html')


def logout_view(request):
    """
    Logs out Django-authenticated users and clears driver session if present.
    """
    if request.user.is_authenticated:
        logout(request)
    if request.session.get('driver_id'):
        request.session.pop('driver_id', None)
    if 'driver_id' in request.session:
        del request.session['driver_id']
    return redirect('homepage')