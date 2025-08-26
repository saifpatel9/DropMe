from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from passenger.models import User
from driver.models import Driver
from django.contrib.auth import logout

def unified_login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Try authenticating as User
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            if user.is_admin:
                return redirect('adminpanel_dashboard')
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
    if request.user.is_authenticated:
        logout(request)
    if 'driver_id' in request.session:
        del request.session['driver_id']
    return redirect('homepage')