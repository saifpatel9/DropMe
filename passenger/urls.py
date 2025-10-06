from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.passenger_dashboard, name='passenger_dashboard'),
    path('cab-homepage/', views.homepage_cab_view, name='homepage'),
    path('signup/', views.signup_view, name='signup'),
    path('choose-ride/', views.choose_ride_view, name='choose_ride'),
    path('book-ride/', views.book_ride_view, name='book_ride'),
    path('logout/', auth_views.LogoutView.as_view(next_page='homepage'), name='logout'),
    path('profile/', views.profile_page, name='profile_page'),
    path('profile/section/<str:section>/', views.profile_section, name='profile_section'),
    path('profile/update-payment-method/', views.update_payment_method, name='update_payment_method'),
    path('profile/update-safety/', views.update_safety_preferences, name='update_safety_preferences'),
    path('profile/section/rating-and-feedback/', views.profile_section, {'section': 'rating-and-feedback'}, name='profile_rating_feedback'),
    path('submit-rating/<int:booking_id>/', views.submit_rating, name='submit_rating'),
    path('update-emergency-contact/', views.update_emergency_contact, name='update_emergency_contact'),
    path('profile/delete/', views.delete_passenger_account, name='passenger_delete_account'),
    path('faq/', views.faq_page, name='faq_page'),
    path('confirm-booking/', views.confirm_booking, name='confirm_booking'),
    path('cancel-booking/', views.cancel_booking, name='cancel_booking'),
    path('waiting-for-driver/<int:ride_request_id>/', views.waiting_for_driver_view, name='waiting_for_driver'),
    path('check-ride-status/<int:ride_request_id>/', views.check_ride_status, name='check_ride_status'),
    path('reassign-next-driver/<int:ride_request_id>/', views.reassign_next_driver, name='reassign_next_driver'),
    path('booking-confirmed/<int:booking_id>/', views.booking_confirmed_view, name='booking_confirmed'),
    path('apply-promo_code/', views.apply_promo_code, name='apply_promo_code'),
    path('apply-promo/', views.apply_promo, name='apply_promo'),
    path("ride-started/<int:booking_id>/", views.ride_started_view, name="ride_started"),
    path("booking-status/<int:booking_id>/", views.booking_status_api, name="booking_status_api"),
    path("driver-arrived/<int:booking_id>/", views.driver_arrived_view, name="driver_arrived"),
    path("ride-completed/<int:booking_id>/", views.ride_completed_view, name="ride_completed"),
]