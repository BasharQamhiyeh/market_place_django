from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Item, ItemPhoto, Category
from .serializers import CategorySerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# ----------------------------------------
# Serializers
# ----------------------------------------
class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPhoto
        fields = ["id", "image", "created_at"]


class ItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Item
        fields = [
            "id", "title", "description", "price",
            "category", "city", "is_active", "is_approved",
            "created_at", "photos",
        ]


class ItemCreateSerializer(serializers.ModelSerializer):
    photos = serializers.ListField(
        child=serializers.ImageField(), required=False, write_only=True
    )

    class Meta:
        model = Item
        fields = [
            "title", "description", "price",
            "category", "city", "photos",
        ]

    def create(self, validated_data):
        photos_data = validated_data.pop("photos", [])
        user = self.context["request"].user
        item = Item.objects.create(user=user, **validated_data)
        for photo in photos_data:
            ItemPhoto.objects.create(item=item, image=photo)
        return item


# ----------------------------------------
# ViewSet
# ----------------------------------------
@extend_schema(tags=["Items"])
class ItemViewSet(viewsets.ModelViewSet):
    """
    Manage marketplace items for mobile API.
    """
    queryset = Item.objects.filter(is_active=True, is_approved=True).select_related("category", "city")
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ItemCreateSerializer
        return ItemSerializer

    def get_queryset(self):
        user = self.request.user

        if self.action == "my_items":
            # Owners see all their items
            return Item.objects.filter(user=user).select_related("category", "city").prefetch_related("photos")

        # Everyone else only sees approved & active items
        return (
            Item.objects.filter(is_active=True, is_approved=True)
            .select_related("category", "city")
            .prefetch_related("photos")
            .order_by("-created_at")
        )

    @extend_schema(
        request=ItemCreateSerializer,
        responses={201: ItemSerializer},
        examples=[
            OpenApiExample(
                "Create Item Example",
                value={
                    "title": "Handmade Cup",
                    "description": "Beautifully crafted ceramic cup",
                    "price": 12.5,
                    "category": 3,
                    "city": 1
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            item = serializer.save()
        read_serializer = ItemSerializer(item, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    # ----------------------------------------
    # /api/items/me/ → list my own items
    # ----------------------------------------
    @extend_schema(
        responses={200: ItemSerializer(many=True)},
        description="List items belonging to the current user."
    )
    @action(detail=False, methods=["get"], url_path="me", permission_classes=[permissions.IsAuthenticated])
    def my_items(self, request):
        items = Item.objects.filter(user=request.user).select_related("category", "city").prefetch_related("photos")
        serializer = ItemSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)

    # ----------------------------------------
    # /api/items/{id}/reactivate/
    # ----------------------------------------
    @extend_schema(
        responses={200: OpenApiResponse(description="Item reactivated successfully.")},
    )
    @action(detail=True, methods=["post"], url_path="reactivate", permission_classes=[permissions.IsAuthenticated])
    def reactivate(self, request, pk=None):
        item = get_object_or_404(Item, pk=pk, user=request.user)
        item.is_active = True
        item.save(update_fields=["is_active"])
        return Response({"message": "Item reactivated successfully."})

    # ----------------------------------------
    # /api/items/{id}/cancel/
    # ----------------------------------------
    @extend_schema(
        responses={200: OpenApiResponse(description="Item cancelled successfully.")},
    )
    @action(detail=True, methods=["post"], url_path="cancel", permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        item = get_object_or_404(Item, pk=pk, user=request.user)
        item.is_active = False
        item.save(update_fields=["is_active"])
        return Response({"message": "Item cancelled successfully."})

    # ----------------------------------------
    # Delete item
    # ----------------------------------------
    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        if item.user != request.user:
            return Response({"detail": "You do not own this item."}, status=403)
        item.delete()
        return Response({"message": "Item deleted successfully."}, status=200)
