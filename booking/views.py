from django.shortcuts import render

def booking_dashboard(request):
    return render(request, 'booking/dashboard.html')  # adjust path if needed
