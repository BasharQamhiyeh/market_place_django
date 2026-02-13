from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from .my_account_messages_api import my_account_conversations_api, my_account_conversation_messages_api, \
    my_account_send_message_api
from .views.api.conversations import api_my_conversations, api_conversation_messages, api_conversation_send
from .views.api.listing import toggle_favorite, feature_listing_api, delete_listing_api, republish_listing_api
from .views.api.search import search_suggestions
from .views.api.wallet import api_wallet_summary
from .views.auth import user_login, user_logout, register, ajax_send_signup_otp, ajax_verify_signup_otp, \
    complete_signup, forgot_password, verify_reset_code, reset_password
from .views.chat import start_conversation, chat_room, user_inbox, start_conversation_request, start_store_conversation
from .views.home import home, home_more_items, home_more_requests
from .views.items import item_list, item_detail, item_create, item_detail_more_similar, item_edit, delete_item, \
    cancel_item, delete_item_photo, my_items, reactivate_item, item_attributes_partial
from .views.misc import about, contact_support, contact_support_done, FAQView, WhyRuknView, PrivacyPolicyView, \
    category_list, subscribe, create_issue_report_ajax, categories_browse
from .views.my_account import my_favorites, edit_profile, change_password, notifications, mark_notifications_read, \
    my_account, my_account_save_info, my_account_noti_fragment, my_account_noti_mark_read, my_account_noti_mark_all_read
from .views.requests import request_detail_more_similar, request_create, request_list, request_detail, request_edit
from .views.stores import store_profile, stores_list, stores_list_partial, store_follow_toggle, \
    submit_store_review_ajax, store_reviews_list
from .views.users import user_profile

urlpatterns = [
    # --- Static ---
    path('about/', about, name='about'),
    path("contact-support/", contact_support, name="contact_support"),
    path("contact-support/done/", contact_support_done, name="contact_support_done"),
    path("faq/", FAQView.as_view(), name="faq"),
    path("why-rukn/", WhyRuknView.as_view(), name="why_rukn"),
    path("privacy/", PrivacyPolicyView.as_view(), name="privacy_policy"),

    # --- Auth ---
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    # --- Homepage / Items ---
    path('', home, name='home'),
    path('items/', item_list, name='item_list'),
    path('item/<int:item_id>/', item_detail, name='item_detail'),
    path('item/create/', item_create, name='create_item'),
    path("home/more-items/", home_more_items, name="home_more_items"),
    path("home/more-requests/", home_more_requests, name="home_more_requests"),
    path("items/<int:item_id>/more-similar/", item_detail_more_similar, name="item_detail_more_similar"),
    path("requests/<int:request_id>/more-similar/", request_detail_more_similar, name="request_detail_more_similar"),


    # # --- Categories & Attributes ---
    path('categories/', category_list, name='category_list'),

    # --- Messaging ---
    path('messages/<int:item_id>/', start_conversation, name='start_conversation'),
    path('chat/<int:conversation_id>/', chat_room, name='chat_room'),
    path('inbox/', user_inbox, name='user_inbox'),
    path("request/<int:request_id>/message/", start_conversation_request, name="start_conversation_request"),
    path("stores/<int:store_id>/start-chat/", start_store_conversation, name="start_store_conversation"),


    # --- Item Management ---
    path('item/<int:item_id>/edit/', item_edit, name='item_edit'),
    path('item/<int:item_id>/delete/', delete_item, name='delete_item'),
    path('item/<int:item_id>/cancel/', cancel_item, name='cancel_item'),
    path('item/<int:item_id>/edit/', item_edit, name='item_edit'),
    path("photo/<int:photo_id>/delete/", delete_item_photo, name="delete_item_photo"),
    path('my-items/', my_items, name='my_items'),
    path('my-items/<int:item_id>/reactivate/', reactivate_item, name='reactivate_item'),

    # --- Favorites ---
    path('favorites/', my_favorites, name='my_favorites'),
    path('favorites/toggle/<int:item_id>/', toggle_favorite, name='toggle_favorite'),

    # --- Profile ---
    path('profile/<int:user_id>/', user_profile, name='user_profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('profile/change-password/', change_password, name='change_password'),

    # --- Notifications ---
    path('notifications/', notifications, name='notifications'),
    path("notifications/mark-read/", mark_notifications_read, name="mark_notifications_read"),

    # --- Search ---
    path("search/suggestions/", search_suggestions, name="search_suggestions"),

    # --- Verification / Password ---

    path("register/", register, name="register"),  # renders the mockup page
    path("auth/send-otp/", ajax_send_signup_otp, name="ajax_send_signup_otp"),
    path("auth/verify-otp/", ajax_verify_signup_otp, name="ajax_verify_signup_otp"),
    path("auth/complete-signup/", complete_signup, name="complete_signup"),


    path('forgot-password/', forgot_password, name='forgot_password'),
    path('verify-reset-code/', verify_reset_code, name='verify_reset_code'),
    path('reset-password/', reset_password, name='reset_password'),

    # --- Newsletter ---
    path('subscribe/', subscribe, name='subscribe'),  # ✅ new

    path("reports/create/", create_issue_report_ajax, name="create_issue_report_ajax"),

    path("items/attributes/<int:category_id>/", item_attributes_partial, name="item_attributes_partial"),

    # REQUEST CREATION + LISTING + DETAIL
    path("request/create/", request_create, name="create_request"),
    path("requests/", request_list, name="request_list"),
    path("request/<int:request_id>/", request_detail, name="request_detail"),
    path("request/<int:request_id>/edit/", request_edit, name="request_edit"),


    path("listing/<int:listing_id>/feature/", feature_listing_api, name="feature_listing_api"),

    path("stores/<int:store_id>/", store_profile, name="store_profile"),
    path("stores/", stores_list, name="stores_list"),
    path("stores/partial/", stores_list_partial, name="stores_list_partial"),

    # AJAX / API endpoints used by JS
    path("store/<int:store_id>/follow-toggle/", store_follow_toggle, name="store_follow_toggle"),

    path("stores/<int:store_id>/review/submit/", submit_store_review_ajax, name="submit_store_review_ajax"),

    path("stores/<int:store_id>/review/list/", store_reviews_list, name="store_reviews_list"),

    path("my-account/", my_account, name="my_account"),
    path("save-info/", my_account_save_info, name="my_account_save_info"),


    path("my-account/noti/fragment/", my_account_noti_fragment, name="my_account_noti_fragment"),
    path("my-account/noti/<int:pk>/read/", my_account_noti_mark_read, name="my_account_noti_mark_read"),
    path("my-account/noti/read-all/", my_account_noti_mark_all_read, name="my_account_noti_mark_all_read"),

    path("api/my-account/conversations/", api_my_conversations, name="api_my_conversations"),
    path("api/my-account/conversations/<int:conversation_id>/messages/", api_conversation_messages,
         name="api_conversation_messages"),
    path("api/my-account/conversations/<int:conversation_id>/send/", api_conversation_send,
         name="api_conversation_send"),

    path("api/wallet/summary/", api_wallet_summary, name="api_wallet_summary"),

    path("listing/<int:listing_id>/delete/", delete_listing_api, name="api_delete_listing"),

    path('listing/<int:listing_id>/republish/', republish_listing_api, name='republish_listing'),

    path('categories/browse/', categories_browse, name='categories_browse'),

    # path('api/', include('marketplace.api_urls')),
]

urlpatterns += [
    path("api/my-account/messages/conversations/", my_account_conversations_api, name="my_account_conversations_api"),
    path("api/my-account/messages/<int:conversation_id>/", my_account_conversation_messages_api, name="my_account_conversation_messages_api"),
    path("api/my-account/messages/<int:conversation_id>/send/", my_account_send_message_api, name="my_account_send_message_api"),
]

# ✅ Static & media for local dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
