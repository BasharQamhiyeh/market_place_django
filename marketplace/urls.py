from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter


urlpatterns = [
    # --- Auth ---
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # --- Homepage / Items ---
    path('', views.home, name='home'),
    path('items/', views.item_list, name='item_list'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('item/create/', views.item_create, name='create_item'),

    # --- Categories & Attributes ---
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.create_category, name='category_create'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),

    # --- Messaging ---
    path('messages/<int:item_id>/', views.start_conversation, name='start_conversation'),
    path('chat/<int:conversation_id>/', views.chat_room, name='chat_room'),
    path('inbox/', views.user_inbox, name='user_inbox'),
    path("request/<int:request_id>/message/", views.start_conversation_request, name="start_conversation_request"),

    # --- Item Management ---
    path('item/edit/<int:item_id>/', views.item_edit, name='item_edit'),
    path('item/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('item/<int:item_id>/cancel/', views.cancel_item, name='cancel_item'),
    path('item/<int:item_id>/edit/', views.item_edit, name='item_edit'),
    path("photo/<int:photo_id>/delete/", views.delete_item_photo, name="delete_item_photo"),
    path('my-items/', views.my_items, name='my_items'),
    path('my-items/<int:item_id>/reactivate/', views.reactivate_item, name='reactivate_item'),

    # --- Favorites ---
    path('favorites/', views.my_favorites, name='my_favorites'),
    path('favorites/toggle/<int:item_id>/', views.toggle_favorite, name='toggle_favorite'),

    # --- Profile ---
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

    # --- Notifications ---
    path('notifications/', views.notifications, name='notifications'),
    path("notifications/mark-read/", views.mark_notifications_read, name="mark_notifications_read"),

    # --- Search ---
    path("search/suggestions/", views.search_suggestions, name="search_suggestions"),

    # --- Verification / Password ---

    path("register/", views.register, name="register"),  # renders the mockup page
    path("auth/send-otp/", views.ajax_send_signup_otp, name="ajax_send_signup_otp"),
    path("auth/verify-otp/", views.ajax_verify_signup_otp, name="ajax_verify_signup_otp"),
    path("auth/complete-signup/", views.complete_signup, name="complete_signup"),


    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/', views.reset_password, name='reset_password'),

    # --- Newsletter ---
    path('subscribe/', views.subscribe, name='subscribe'),  # ✅ new

    path('contact/', views.contact, name='contact'),

    path('item/<int:item_id>/report/', views.report_issue, name='report_issue'),

    path("items/attributes/<int:category_id>/", views.item_attributes_partial, name="item_attributes_partial"),

    # REQUEST CREATION + LISTING + DETAIL
    path("request/create/", views.request_create, name="create_request"),
    path("requests/", views.request_list, name="request_list"),
    path("request/<int:request_id>/", views.request_detail, name="request_detail"),


    # path('api/', include('marketplace.api_urls')),
]

# ✅ Static & media for local dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
