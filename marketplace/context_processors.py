from django.db.models import Q
from .models import Notification, Message

def navbar_counters(request):
    if not request.user.is_authenticated:
        return {}

    unread_notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).count()

    unread_messages = Message.objects.filter(
        Q(conversation__buyer=request.user) | Q(conversation__seller=request.user),
        is_read=False
    ).exclude(sender=request.user).count()

    return {
        "unread_notifications": unread_notifications,
        "unread_messages": unread_messages,
    }
