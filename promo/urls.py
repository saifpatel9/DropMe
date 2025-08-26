from django.urls import path
from . import views

urlpatterns = [
    path('', views.promo_dashboard, name='promo_dashboard'),
    path('add/', views.add_promo, name='add_promo'),
    path('edit/<int:promo_id>/', views.edit_promo, name='edit_promo'),
    path('delete/<int:promo_id>/', views.delete_promo, name='delete_promo'),
]