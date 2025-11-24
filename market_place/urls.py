from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('_nested_admin/', include('nested_admin.urls')),  # ✅ add this line
    path('i18n/', include('django.conf.urls.i18n')),
    # path('api/', include('marketplace.api_urls')),
]

urlpatterns += [
    # OpenAPI schema endpoint
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),

    # Swagger UI
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="swagger-ui"),

    # ReDoc UI
    path("api/redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="redoc"),
]

if settings.DEBUG or getattr(settings, "IS_RENDER", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path('', include('marketplace.urls')),
)
