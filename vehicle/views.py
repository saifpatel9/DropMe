from django.shortcuts import render

def vehicle_dashboard(request):
    return render(request, 'vehicle/dashboard.html')  # adjust path if needed
