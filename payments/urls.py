from django.urls import path
from . import views

urlpatterns = [
    path('', views.payments_dashboard, name='payments_dashboard'),
]
