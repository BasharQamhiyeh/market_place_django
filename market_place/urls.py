from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def redirect_lang(request, path=None):
    return redirect('/', permanent=True)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('_nested_admin/', include('nested_admin.urls')),

    # redirect old language-prefixed URLs
    path('en/', redirect_lang),
    path('en/<path:path>/', redirect_lang),
    path('ar/', redirect_lang),
    path('ar/<path:path>/', redirect_lang),

    # main app without language prefix
    path('', include('marketplace.urls')),

    # OpenAPI schema endpoint
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="redoc"),
]

if settings.DEBUG or getattr(settings, "IS_RENDER", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
