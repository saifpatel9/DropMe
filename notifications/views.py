from django.shortcuts import render

def notifications_dashboard(request):
    return render(request, 'notifications/dashboard.html')  # adjust path if needed
