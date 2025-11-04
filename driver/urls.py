from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_driver_list, name='driver_dashboard'),
    path('<int:driver_id>/', views.admin_driver_detail, name='driver_detail'),
    path('driver_homepage/', views.driver_homepage_cab_view, name='driver_homepage'),
    path('accept-ride/<int:ride_request_id>/', views.accept_ride, name='accept_ride'),
    path('reject_ride/<int:ride_request_id>/', views.reject_ride, name='reject_ride'),
    path('check-assignment/', views.check_driver_assignment, name='check_driver_assignment'),
    path('driver/profile/<int:driver_id>/', views.driver_profile_view, name='driver_profile'),
    path('rides/', views.driver_rides_view, name='driver_rides'),
    path("driver/profile/", views.driver_profile_view, name="driver_profile"),
    path('rides/end/<int:booking_id>/', views.end_ride_view, name='end_ride'),
    path('rides/start/<int:booking_id>/', views.start_ride_view, name='start_ride'),
    path('rides/arrived/<int:booking_id>/', views.arrived_ride_view, name='arrived_ride'),
    path('driver/earnings/', views.driver_earnings_view, name='driver_earnings'),
    path('driver/ride-request/', views.driver_ride_request_page, name='driver_ride_request'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path("driver/edit-profile/", views.driver_edit_profile_view, name="driver_edit_profile"),
    path('ratings/', views.driver_rating_page, name='driver_rating_page'),
    path('submit-rating/', views.submit_driver_rating, name='submit_driver_rating'),
    path('api/assigned-requests/', views.api_assigned_requests, name='api_assigned_requests'),
    path('api/ride-request/<int:ride_request_id>/', views.api_ride_request_details, name='api_ride_request_details'),
]
