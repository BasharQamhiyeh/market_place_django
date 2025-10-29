from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]

# ✅ Always serve /media/ on Render or local testing
if settings.DEBUG or getattr(settings, "IS_RENDER", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ✅ Language-prefixed routes (keep these after)
urlpatterns += i18n_patterns(
    path('', include('marketplace.urls')),
)
