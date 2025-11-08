# marketplace/api_serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    Category, Attribute, AttributeOption,
    Item, ItemPhoto, ItemAttributeValue, City,
    Conversation, Message, Notification, Favorite,
    IssueReport, Subscriber, PhoneVerificationCode
)
from .validators import validate_no_links_or_html

User = get_user_model()

# -------------------------
# User & Auth
# -------------------------
class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_id", "username", "first_name", "last_name", "show_phone"]

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_id", "username", "first_name", "last_name", "email", "phone", "show_phone"]

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ["username", "phone", "email", "password", "first_name", "last_name", "show_phone"]

    def validate_phone(self, phone):
        # Normalize 07xxxxxxxx -> 9627xxxxxxxx (same as forms.py)
        p = phone.strip().replace(" ", "")
        import re
        if re.fullmatch(r"07\d{8}", p):
            return "962" + p[1:]
        if not re.fullmatch(r"9627\d{8}", p):
            raise serializers.ValidationError("Phone must be 07xxxxxxxx or 9627xxxxxxxx.")
        return p

    def create(self, validated_data):
        pwd = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(pwd)
        user.save()
        return user

# -------------------------
# Taxonomy (categories/attributes)
# -------------------------
class AttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ["id", "value_en", "value_ar"]

class AttributeSerializer(serializers.ModelSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)
    class Meta:
        model = Attribute
        fields = ["id", "name_en", "name_ar", "input_type", "is_required", "options"]

class CategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name_en", "name_ar", "parent_id"]

class CategoryTreeSerializer(serializers.ModelSerializer):
    subcategories = CategoryBriefSerializer(many=True, read_only=True)
    attributes = AttributeSerializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = ["id", "name_en", "name_ar", "description", "parent_id", "subcategories", "attributes"]

# -------------------------
# Cities
# -------------------------
class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name_en", "name_ar"]

# -------------------------
# Item & dynamic attributes
# -------------------------
class ItemPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPhoto
        fields = ["id", "image", "created_at"]

class ItemAttributeValueSerializer(serializers.ModelSerializer):
    attribute_id = serializers.IntegerField()
    attribute_name = serializers.SerializerMethodField()

    class Meta:
        model = ItemAttributeValue
        fields = ["id", "attribute_id", "attribute_name", "value"]

    def get_attribute_name(self, obj):
        lang = self.context.get("lang")
        a = obj.attribute
        if not a: return None
        return a.name_ar if lang == "ar" else a.name_en

class ItemListSerializer(serializers.ModelSerializer):
    category = CategoryBriefSerializer(read_only=True)
    user = UserPublicSerializer(read_only=True)
    photos = ItemPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Item
        fields = ["id", "title", "condition", "price", "description", "city_id",
                  "category", "user", "photos", "is_approved", "is_active", "created_at"]

class ItemDetailSerializer(serializers.ModelSerializer):
    category = CategoryBriefSerializer(read_only=True)
    user = UserPublicSerializer(read_only=True)
    photos = ItemPhotoSerializer(many=True, read_only=True)
    attribute_values = ItemAttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = Item
        fields = ["id", "title", "condition", "price", "description", "city_id",
                  "category", "user", "photos", "attribute_values",
                  "is_approved", "is_active", "created_at"]

class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False),
        write_only=True, required=False
    )
    attribute_values = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False,
        help_text='[{"attribute_id":1, "value":"Red"}, ...]'
    )

    # declare them so DRF keeps them in validated_data
    city_id = serializers.IntegerField(write_only=True, required=False)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Item
        fields = [
            "title", "condition", "price", "description",
            "city_id", "category_id", "images", "attribute_values"
        ]

    def validate_images(self, images):
        """
        Extra validation on uploaded images for API.
        """
        MAX_MB = 5
        MAX_BYTES = MAX_MB * 1024 * 1024
        ALLOWED_EXTS = {"jpg", "jpeg", "png", "webp"}

        for img in images:
            if img.size > MAX_BYTES:
                raise serializers.ValidationError(
                    f"File {img.name} is too large (max {MAX_MB} MB)."
                )
            name = getattr(img, "name", "") or ""
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext not in ALLOWED_EXTS:
                raise serializers.ValidationError(
                    f"File {name} has an unsupported type. "
                    f"Allowed: {', '.join(sorted(ALLOWED_EXTS))}."
                )
        return images

    def validate_title(self, value):
        return validate_no_links_or_html(value)

    def validate_description(self, value):
        if value is None:
            return value
        return validate_no_links_or_html(value)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attr_values = attrs.get("attribute_values", [])

        for av in attr_values:
            if isinstance(av, dict) and "value" in av and isinstance(av["value"], str):
                av["value"] = validate_no_links_or_html(av["value"])

        return attrs

    def create(self, validated):
        request = self.context["request"]

        print("=== DEBUG: FILES RECEIVED ===")
        print("FILES keys:", list(request.FILES.keys()))
        for k, v in request.FILES.items():
            print(f" - {k} → {v.name} ({v.size} bytes)")

        print("=== DEBUG: DATA RECEIVED ===")
        print("DATA keys:", list(request.data.keys()))
        print("DATA:", request.data)



        validated["user"] = request.user
        validated["is_approved"] = False
        validated["is_active"] = True

        # ✅ map FK IDs to model fields
        if "category_id" in validated:
            validated["category"] = Category.objects.get(pk=validated.pop("category_id"))
        if "city_id" in validated:
            validated["city"] = City.objects.filter(pk=validated.pop("city_id")).first()

        item = Item.objects.create(
            **{k: v for k, v in validated.items() if k not in ("images", "attribute_values")}
        )

        # ✅ Handle images from either format
        uploaded_files = validated.get("images", [])
        if not uploaded_files:  # in case Flutter sends images[0], images[1], ...
            uploaded_files = [
                file for key, file in request.FILES.items() if key.startswith("images")
            ]

        for img in uploaded_files:
            ItemPhoto.objects.create(item=item, image=img)

        # ✅ create attribute values
        for av in validated.get("attribute_values", []):
            aid = int(av.get("attribute_id"))
            val = (av.get("value") or "").strip()
            if val:
                ItemAttributeValue.objects.create(item=item, attribute_id=aid, value=val)

        return item

    def update(self, instance, validated):
        # update simple fields
        for f in ["title", "condition", "price", "description"]:
            if f in validated:
                setattr(instance, f, validated[f])

        # ✅ handle city/category changes too
        if "city_id" in validated:
            instance.city = City.objects.filter(pk=validated["city_id"]).first()
        if "category_id" in validated:
            instance.category = Category.objects.get(pk=validated["category_id"])

        instance.is_approved = False
        instance.was_edited = True
        instance.save()

        # ✅ replace attribute values
        if "attribute_values" in validated:
            ItemAttributeValue.objects.filter(item=instance).delete()
            for av in validated.get("attribute_values") or []:
                aid = int(av.get("attribute_id"))
                val = (av.get("value") or "").strip()
                if val:
                    ItemAttributeValue.objects.create(item=instance, attribute_id=aid, value=val)

        # ✅ add any new images
        for img in validated.get("images", []):
            ItemPhoto.objects.create(item=instance, image=img)

        return instance



# -------------------------
# Favorites
# -------------------------
class FavoriteSerializer(serializers.ModelSerializer):
    item = ItemListSerializer(read_only=True)
    class Meta:
        model = Favorite
        fields = ["id", "item", "created_at"]

# -------------------------
# Messaging & Notifications
# -------------------------
class ConversationSerializer(serializers.ModelSerializer):
    buyer = UserPublicSerializer(read_only=True)
    seller = UserPublicSerializer(read_only=True)
    item = ItemListSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "item", "buyer", "seller", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserPublicSerializer(read_only=True)

    def validate_body(self, value):
        return validate_no_links_or_html(value)

    class Meta:
        model = Message
        fields = ["id", "conversation_id", "sender", "body", "created_at"]

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "user_id", "body", "is_read", "created_at"]

# -------------------------
# Misc
# -------------------------
class IssueReportSerializer(serializers.ModelSerializer):

    def validate_message(self, value):
        return validate_no_links_or_html(value)

    class Meta:
        model = IssueReport
        fields = ["id", "item_id", "message", "status", "created_at"]

class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ["id", "email", "subscribed_at"]
