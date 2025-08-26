from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_dashboard, name='notifications_dashboard'),
]
