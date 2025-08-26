from django.shortcuts import render

def payments_dashboard(request):
    return render(request, 'payments/dashboard.html')  # adjust path if needed
