from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('', views.item_list, name='item_list'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('create/', views.item_create, name='create_item'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.create_category, name='category_create'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('messages/<int:item_id>/', views.start_conversation, name='start_conversation'),
    path('chat/<int:conversation_id>/', views.chat_room, name='chat_room'),
    path('inbox/', views.user_inbox, name='user_inbox'),
    path('item/edit/<int:item_id>/', views.item_edit, name='item_edit'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('my-items/', views.my_items, name='my_items'),
    path('my-items/<int:item_id>/reactivate/', views.reactivate_item, name='reactivate_item'),
    path('item/<int:item_id>/edit/', views.item_edit, name='item_edit'),
    path("photo/<int:photo_id>/delete/", views.delete_item_photo, name="delete_item_photo"),
    path('item/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('item/<int:item_id>/cancel/', views.cancel_item, name='cancel_item'),
    path('favorites/', views.my_favorites, name='my_favorites'),
    path('favorites/toggle/<int:item_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path("search/suggestions/", views.search_suggestions, name="search_suggestions"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)