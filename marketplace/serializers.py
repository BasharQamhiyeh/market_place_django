from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Item, ItemPhoto, Category, City,
    # Optional models below; if your app uses different names, tweak here
    Attribute, AttributeOption, ItemAttributeValue,
    Conversation, Message, Favorite, Notification
)

User = get_user_model()

# ---------- User ----------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_id", "username", "first_name", "last_name", "email", "phone", "show_phone", "is_active"]
        read_only_fields = ["user_id", "username", "is_active"]

# ---------- City ----------
class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name_en", "name_ar", "is_active"]

# ---------- Category ----------
class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Category
        fields = ["id", "name_en", "name_ar", "parent"]

# ---------- Attributes (dynamic per category) ----------
class AttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ["id", "value_en", "value_ar"]

class AttributeSerializer(serializers.ModelSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)
    class Meta:
        model = Attribute
        fields = ["id", "name_en", "name_ar", "input_type", "is_required", "options"]

# ---------- Photos ----------
class PhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    class Meta:
        model = ItemPhoto
        fields = ["id", "image", "created_at"]

# ---------- Items ----------
class ItemListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    city = CitySerializer(read_only=True)
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Item
        fields = [
            "id", "title", "description", "price", "condition",
            "category", "city", "is_active", "is_approved",
            "created_at", "photos",
        ]

class ItemCreateSerializer(serializers.ModelSerializer):
    photos = serializers.ListField(child=serializers.ImageField(), required=False, write_only=True)
    attributes = serializers.JSONField(required=False, write_only=True)  # [{"id":..., "value":"..."}]

    class Meta:
        model = Item
        fields = ["title", "description", "price", "condition", "category", "city", "photos", "attributes"]

    def create(self, validated_data):
        photos = validated_data.pop("photos", [])
        attrs = validated_data.pop("attributes", [])
        user = self.context["request"].user

        item = Item.objects.create(user=user, is_approved=False, is_active=True, **validated_data)

        for img in photos:
            ItemPhoto.objects.create(item=item, image=img)

        for entry in (attrs or []):
            try:
                attr_id = int(entry.get("id"))
                val = str(entry.get("value", "")).strip()
                if val:
                    ItemAttributeValue.objects.create(item=item, attribute_id=attr_id, value=val)
            except Exception:
                continue

        return item

# ---------- Favorites ----------
class FavoriteSerializer(serializers.ModelSerializer):
    item = ItemListSerializer(read_only=True)
    class Meta:
        model = Favorite
        fields = ["id", "item", "created_at"]

# ---------- Conversations / Messages ----------
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ["id", "sender", "content", "created_at", "is_read"]

class ConversationSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    item = ItemListSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "item", "buyer", "seller", "created_at", "last_message"]

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        return MessageSerializer(msg).data if msg else None

# ---------- Notifications ----------
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "body", "is_read", "created_at", "url"]
