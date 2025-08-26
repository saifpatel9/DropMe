from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicle_dashboard, name='vehicle_dashboard'),
]
