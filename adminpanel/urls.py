from django.urls import path, include
from django.urls import path
from . import views
from driver import views as driver_views
from services import views as services_views
from .views import add_fareslab, edit_fareslab

urlpatterns = [

    path('', views.adminpanel_dashboard, name='adminpanel_dashboard'),
    path('login/', views.login_view, name='login'),
    # Passenger URLs

    path('passengers/', views.admin_passengers, name='admin_passengers'),
    path('passengers/view/<int:user_id>/', views.view_passenger, name='view_passenger'),
    path('passengers/edit/<int:user_id>/', views.edit_passenger, name='edit_passenger'),
    path('passengers/delete/<int:user_id>/', views.delete_passenger, name='delete_passenger'),
    path('passengers/decline/<int:user_id>/', views.decline_passenger, name='decline_passenger'),
    # Driver URLs

    path('drivers/', views.admin_drivers, name='admin_drivers'),
    path('add/', views.add_driver, name='add_driver'),
    path('drivers/view/<int:driver_id>/', views.view_driver, name='view_driver'),
    path('drivers/edit/<int:driver_id>/', views.edit_driver, name='edit_driver'),
    path('drivers/decline/<int:driver_id>/', views.decline_driver, name='decline_driver'),
    path('drivers/delete/<int:driver_id>/', views.delete_driver, name='delete_driver'),
    path('drivers/history/<int:driver_id>/', views.view_driver_history, name='view_driver_history'),
    path('drivers/documents/<int:driver_id>/', views.view_driver_documents, name='view_driver_documents'),
    path("drivers/documents/<int:driver_id>/update-status/",views.update_driver_document_status,name="update_driver_document_status",),
    path('drivers/<int:driver_id>/', driver_views.admin_driver_detail, name='driver_detail'),
    
    # Booking URLs
    path('bookings/', views.admin_bookings, name='admin_bookings'),

    # Vehicle URLs
    path('vehicles/', views.vehicle_dashboard, name='vehicle_dashboard'),
    path('vehicles/add/', views.add_vehicle, name='add_vehicle'),
    path('vehicles/view/<int:vehicle_id>/', views.view_vehicle, name='view_vehicle'),
    path('vehicles/edit/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    path('vehicles/delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),

    # Service URLs
    path('services/', views.service_dashboard, name='service_dashboard'),
    path('services/add/', views.add_service, name='add_service'),
    path('services/edit/<int:service_id>/', views.edit_service, name='edit_service'),
    path('services/view/<int:service_id>/', views.view_service, name='view_service'),
    path('services/delete/<int:service_id>/', views.delete_service, name='delete_service'),
    path('services/decline/<int:service_id>/', views.decline_service, name='decline_service'),
    path('rental/', services_views.rental_dashboard, name='rental_dashboard'),
    path('rental/package/add/', services_views.add_rental_package, name='add_rental_package'),
    path('rental/package/edit/<int:pk>/', services_views.edit_rental_package, name='edit_rental_package'),
    path('rental/package/delete/<int:pk>/', services_views.delete_rental_package, name='delete_rental_package'),
    path('rental/service/add/', services_views.add_rental_service, name='add_rental_service'),
    path('rental/service/edit/<int:pk>/', services_views.edit_rental_service, name='edit_rental_service'),
    path('rental/service/delete/<int:pk>/', services_views.delete_rental_service, name='delete_rental_service'),
    path('services/add-slab/', add_fareslab, name='add_fareslab'),
    path('services/edit-slab/<int:slab_id>/', edit_fareslab, name='edit_fareslab'),

    # Promo URLs
    path('promos/', include(('promo.urls', 'promo'), namespace='promo')),

    # Wallet URLs
    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),
    path('wallet/transactions/<int:wallet_id>/', views.wallet_transactions, name='wallet_transactions'),
    path('wallet/redeems/<int:wallet_id>/', views.wallet_redeems, name='wallet_redeems'),
    path('wallet/payment/<int:wallet_payment_id>/', views.view_wallet_payment, name='view_wallet_payment'),
    path('wallet/<int:wallet_id>/transactions/', views.wallet_transactions, name='wallet_transactions'),
    path('wallet/<int:wallet_id>/redeems/', views.wallet_redeems, name='wallet_redeems'),
    path('wallet/payment/<int:wallet_payment_id>/', views.view_wallet_payment, name='view_wallet_payment'),

    # Rating URLs
    path('ratings/', views.rating_dashboard, name='rating_dashboard'),
    path('rating/passenger/', views.passenger_rating_view, name='passenger_ratings_list'),
    path('rating/driver/', views.driver_rating_view, name='driver_ratings_list'),       
    path('rating/passenger/<int:pk>/', views.passenger_rating_detail, name='passenger_rating_detail'),
    path('rating/driver/<int:pk>/', views.driver_rating_detail, name='driver_rating_detail'),       

    # FAQ URLs
    path('faq/', views.faq_dashboard, name='faq_dashboard'),
    path('faq/add/', views.add_faq, name='add_faq'),
    path('faq/edit/<int:faq_id>/', views.edit_faq, name='edit_faq'),
    path('faq/delete/<int:faq_id>/', views.delete_faq, name='delete_faq'), 
    path('faq/detail/<int:faq_id>/', views.faq_detail, name='faq_detail'),

    # Payments URLs
    path("payments/dashboard/", views.payment_dashboard, name="payment_dashboard"),
    path("payments/<int:payment_id>/", views.view_payment, name="view_payment"),
    path("payments/<int:payment_id>/refund/", views.refund_payment, name="refund_payment"),

    # Feedback URLs
    path('feedback/', views.feedback_dashboard, name='feedback_dashboard'),
    #path('feedback/edit/<int:feedback_id>/', views.edit_feedback, name='edit_feedback'),
    #path('feedback/delete/<int:feedback_id>/', views.delete_feedback, name='delete_feedback'),

]

