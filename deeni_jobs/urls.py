"""
URL configuration for deeni_jobs project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/locations/', include('locations.urls')),
    path('api/v1/profile-data/', include('profiles.reference_urls')),
    path('api/v1/profiles/', include('profiles.urls')),
    path('api/v1/employers/', include('employers.urls')),
    path('api/v1/jobs/', include('jobs.urls')),
    path('api/v1/applications/', include('applications.urls')),
    path('api/v1/admin/', include('admin_panel.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
]

if settings.DEBUG and not settings.USE_R2_STORAGE:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
