"""
URL configuration for market_place project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# ---------------------------------------------------
# Base URL patterns
# ---------------------------------------------------
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # language switcher
]

# ---------------------------------------------------
# Internationalized patterns
# ---------------------------------------------------
urlpatterns += i18n_patterns(
    path('', include('marketplace.urls')),
)

# ---------------------------------------------------
# Serve media files in development and Render testing
# ---------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
