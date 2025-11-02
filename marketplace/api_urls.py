from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_items import ItemViewSet, CategoryViewSet, CityViewSet
from .api_conversations import ConversationViewSet
from .api_favorites import FavoriteViewSet
from .api_notifications import NotificationViewSet
from .api_auth import LoginView, RefreshView
from .api_auth_mobile import RequestCodeAPI, VerifyCodeAPI
from .api_auth_password import ForgotPasswordAPI, VerifyResetCodeAPI, ResetPasswordAPI

router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='items')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'cities', CityViewSet, basename='cities')
router.register(r'conversations', ConversationViewSet, basename='conversations')
router.register(r'favorites', FavoriteViewSet, basename='favorites')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),

    # auth
    path('auth/login/',   LoginView.as_view(),   name='api_login'),
    path('auth/refresh/', RefreshView.as_view(), name='api_refresh'),

    # mobile register by phone code
    path('auth/register/request-code/', RequestCodeAPI.as_view()),
    path('auth/register/verify/',       VerifyCodeAPI.as_view()),

    # password reset by phone
    path('auth/password/forgot/', ForgotPasswordAPI.as_view()),
    path('auth/password/verify/', VerifyResetCodeAPI.as_view()),
    path('auth/password/reset/',  ResetPasswordAPI.as_view()),
]
