from django.db.models import Q
from .models import Notification, Message, Favorite


def navbar_counters(request):
    """
    Provides counts & recent lists for the top bar:
    - unread_messages
    - unread_notifications
    - favorite_count
    - recent_messages
    - recent_notifications
    - recent_favorites
    """
    if not request.user.is_authenticated:
        return {}

    user = request.user

    # Unread notifications
    unread_notifications = Notification.objects.filter(
        user=user, is_read=False
    ).count()

    # Unread messages (user is buyer or seller, but exclude own sent messages)
    unread_messages = Message.objects.filter(
        Q(conversation__buyer=user) | Q(conversation__seller=user),
        is_read=False,
    ).exclude(sender=user).count()

    # Last 6 notifications
    recent_notifications = (
        Notification.objects.filter(user=user)
        .select_related("item")
        .order_by("-created_at")[:6]
    )

    # Last 6 messages
    recent_messages = (
        Message.objects.filter(
            Q(conversation__buyer=user) | Q(conversation__seller=user)
        )
        .select_related("conversation", "sender", "conversation__item")
        .order_by("-created_at")[:6]
    )

    # Favorites count and recent favorites
    fav_qs = (
        Favorite.objects.filter(user=user)
        .select_related("item", "item__category")
        .prefetch_related("item__photos")
        .order_by("-created_at")
    )
    favorite_count = fav_qs.count()
    recent_favorites = fav_qs[:5]

    return {
        "unread_notifications": unread_notifications,
        "unread_messages": unread_messages,
        "recent_notifications": recent_notifications,
        "recent_messages": recent_messages,
        "favorite_count": favorite_count,
        "recent_favorites": recent_favorites,
    }
