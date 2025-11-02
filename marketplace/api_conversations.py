from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Conversation, Message, Item
from django.contrib.auth import get_user_model

User = get_user_model()


# --------------------------
# 📱 Serializers
# --------------------------
class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender_name", "content", "created_at", "is_read"]


class ConversationSerializer(serializers.ModelSerializer):
    item_title = serializers.CharField(source="item.title", read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "item_title", "buyer_id", "seller_id", "created_at", "last_message"]

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by("-created_at").first()
        return last_msg.content if last_msg else None


class StartConversationSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(help_text="ID of the item to start a chat about")
    message = serializers.CharField(help_text="First message content")


# --------------------------
# 📱 ViewSet
# --------------------------
@extend_schema(tags=["Messaging"])
class ConversationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    # ✅ GET /api/conversations/
    @extend_schema(
        responses={200: ConversationSerializer(many=True)},
        description="List all conversations of the current user."
    )
    def list(self, request):
        user = request.user
        conversations = Conversation.objects.filter(
            buyer=user
        ) | Conversation.objects.filter(seller=user)
        conversations = conversations.distinct().order_by("-created_at").prefetch_related("item")
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)

    # ✅ POST /api/conversations/ → start chat
    @extend_schema(
        request=StartConversationSerializer,
        responses={201: ConversationSerializer},
        examples=[
            OpenApiExample(
                "Example Request",
                value={"item_id": 12, "message": "Hi, is this still available?"},
                request_only=True,
            )
        ],
    )
    def create(self, request):
        item_id = request.data.get("item_id")
        message_text = request.data.get("message")
        user = request.user

        if not all([item_id, message_text]):
            return Response({"detail": "item_id and message are required."}, status=400)

        item = get_object_or_404(Item, pk=item_id)
        if item.user == user:
            return Response({"detail": "You cannot message yourself."}, status=400)

        conversation, created = Conversation.objects.get_or_create(
            item=item,
            buyer=user,
            seller=item.user,
        )

        Message.objects.create(conversation=conversation, sender=user, content=message_text)

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=201)

    # ✅ GET /api/conversations/{id}/messages/
    @extend_schema(
        responses={200: MessageSerializer(many=True)},
        description="List all messages in a conversation."
    )
    @action(detail=True, methods=["get"], url_path="messages")
    def get_messages(self, request, pk=None):
        conv = get_object_or_404(Conversation, pk=pk)
        if request.user not in [conv.buyer, conv.seller]:
            return Response({"detail": "Not your conversation."}, status=403)

        messages = conv.messages.order_by("created_at")
        serializer = MessageSerializer(messages, many=True)
        # mark other user's messages as read
        Message.objects.filter(conversation=conv).exclude(sender=request.user).update(
            is_read=True, read_at=timezone.now()
        )
        return Response(serializer.data)

    # ✅ POST /api/conversations/{id}/messages/
    @extend_schema(
        request={"type": "object", "properties": {"content": {"type": "string"}}},
        responses={201: MessageSerializer},
        examples=[OpenApiExample("Example", value={"content": "I'm interested!"})],
    )
    @action(detail=True, methods=["post"], url_path="messages")
    def send_message(self, request, pk=None):
        conv = get_object_or_404(Conversation, pk=pk)
        if request.user not in [conv.buyer, conv.seller]:
            return Response({"detail": "Not your conversation."}, status=403)

        content = request.data.get("content")
        if not content:
            return Response({"detail": "Message content required."}, status=400)

        msg = Message.objects.create(conversation=conv, sender=request.user, content=content)
        serializer = MessageSerializer(msg)
        return Response(serializer.data, status=201)
