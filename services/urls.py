from django.urls import path
from . import views

app_name = 'adminpanel'  # 👈 namespace for reverse URL lookup

urlpatterns = [
    # Rental Dashboard
    path('rental/', views.rental_dashboard, name='rental_dashboard'),

    # Rental Packages
    path('rental/packages/add/', views.add_rental_package, name='add_rental_package'),
    path('rental/packages/edit/<int:pk>/', views.edit_rental_package, name='edit_rental_package'),
    path('rental/packages/delete/<int:pk>/', views.delete_rental_package, name='delete_rental_package'),

    # Rental Services
    path('rental/services/add/', views.add_rental_service, name='add_rental_service'),
    path('rental/services/edit/<int:pk>/', views.edit_rental_service, name='edit_rental_service'),
    path('rental/services/delete/<int:pk>/', views.delete_rental_service, name='delete_rental_service'),
]