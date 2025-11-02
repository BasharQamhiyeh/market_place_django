# marketplace/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    RegisterAPI, LoginAPI, ProfileAPI, ChangePasswordAPI,
    SendVerifyCodeAPI, VerifyPhoneAPI, ForgotPasswordAPI, VerifyResetCodeAPI, ResetPasswordAPI,
    CategoryViewSet, AttributeViewSet, CityViewSet,
    ItemViewSet, MyItemsAPI, ItemPhotoDeleteAPI,
    FavoriteViewSet,
    ConversationViewSet, MessageViewSet,
    NotificationViewSet,
    IssueReportAPI, SubscribeAPI
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"attributes", AttributeViewSet, basename="attributes")
router.register(r"cities", CityViewSet, basename="cities")
router.register(r"items", ItemViewSet, basename="items")
router.register(r"favorites", FavoriteViewSet, basename="favorites")
router.register(r"conversations", ConversationViewSet, basename="conversations")
router.register(r"messages", MessageViewSet, basename="messages")
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"issue-reports", IssueReportAPI, basename="issues")
router.register(r"subscribe", SubscribeAPI, basename="subscribe")

urlpatterns = [
    # Auth
    path("auth/register/", RegisterAPI.as_view(), name="api_register"),
    path("auth/login/", LoginAPI.as_view(), name="api_login"),
    path("auth/profile/", ProfileAPI.as_view(), name="api_profile"),
    path("auth/change-password/", ChangePasswordAPI.as_view(), name="api_change_password"),

    # Phone codes
    path("auth/send-verify-code/", SendVerifyCodeAPI.as_view(), name="api_send_verify_code"),
    path("auth/verify-phone/", VerifyPhoneAPI.as_view(), name="api_verify_phone"),

    # Forgot/reset
    path("auth/forgot-password/", ForgotPasswordAPI.as_view(), name="api_forgot_password"),
    path("auth/verify-reset-code/", VerifyResetCodeAPI.as_view(), name="api_verify_reset_code"),
    path("auth/reset-password/", ResetPasswordAPI.as_view(), name="api_reset_password"),

    # Items (mine) + photo delete
    path("items/mine/", MyItemsAPI.as_view(), name="api_my_items"),
    path("items/photos/<int:pk>/", ItemPhotoDeleteAPI.as_view(), name="api_delete_item_photo"),

    # Routers
    path("", include(router.urls)),
]
