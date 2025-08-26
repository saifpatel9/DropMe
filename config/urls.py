# dropme_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('driver/', include('driver.urls')),
    path('booking/', include('booking.urls')),
    path('vehicle/', include('vehicle.urls')),
    path('panel/', include('adminpanel.urls')), 
    path('payments/', include('payments.urls')),
    path('notifications/', include('notifications.urls')),
    path('documents/', include('documents.urls')),
    path('services/', include('services.urls')),
    path('passenger/', include('passenger.urls')),
    path('', include('accounts.urls')),
    path('', RedirectView.as_view(url='/panel/login/', permanent=False)),
    path('driver/', include(('driver.urls', 'driver'), namespace='driver')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)