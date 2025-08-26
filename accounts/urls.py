from django.urls import path
from .views import unified_login_view
from .views import logout_view

urlpatterns = [
    path('login/', unified_login_view, name='login'),
    path('logout/',logout_view, name='logout'),
]