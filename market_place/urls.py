from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('_nested_admin/', include('nested_admin.urls')),  # ✅ add this line
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # raw OpenAPI schema
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/auth/', include('marketplace.api_auth')),
    path('api/', include('marketplace.api_urls')),
]

if settings.DEBUG or getattr(settings, "IS_RENDER", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path('', include('marketplace.urls')),
)
