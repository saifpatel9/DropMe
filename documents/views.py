from django.shortcuts import render

def documents_dashboard(request):
    return render(request, 'documents/dashboard.html')  # adjust path if needed
