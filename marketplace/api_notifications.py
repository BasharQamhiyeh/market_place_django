from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Notification
from .serializers import ItemSerializer  # only if notifications include item info


@extend_schema(tags=["Notifications"])
class NotificationViewSet(viewsets.ViewSet):
    """
    Manage user notifications for the mobile API.
    """
    permission_classes = [permissions.IsAuthenticated]

    # ----------------------------------------
    # ✅ GET /api/me/notifications/
    # ----------------------------------------
    @extend_schema(
        responses={200: OpenApiResponse(description="List of user notifications.")},
        description="List notifications for the current user (most recent first).",
    )
    @action(detail=False, methods=["get"], url_path="me/notifications")
    def list_notifications(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
        data = [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "created_at": n.created_at,
                "is_read": n.is_read,
            }
            for n in notifications
        ]

        # Mark unread as read automatically (like your web version)
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())

        return Response(data, status=status.HTTP_200_OK)

    # ----------------------------------------
    # ✅ POST /api/notifications/{id}/read/
    # ----------------------------------------
    @extend_schema(
        responses={200: OpenApiResponse(description="Notification marked as read.")},
        examples=[OpenApiExample("Example", value={"message": "Marked as read."})],
    )
    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return Response({"message": "Marked as read."}, status=status.HTTP_200_OK)
