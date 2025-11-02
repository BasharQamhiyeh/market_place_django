from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework import serializers
# marketplace/api_views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.shortcuts import get_object_or_404

from .models import Item, Category, City, Attribute
from .serializers import (
    ItemListSerializer, ItemCreateSerializer,
    CategorySerializer, CitySerializer,
    AttributeSerializer
)


User = get_user_model()

# -------------------------------
# 📱 Serializer for profile data
# -------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'first_name', 'last_name',
            'email', 'phone', 'show_phone', 'phone_verified',
        ]
        read_only_fields = ['user_id', 'username', 'phone_verified']


# -------------------------------
# 📱 Serializer for password change
# -------------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()


# =====================================================
# User ViewSet
# =====================================================
@extend_schema(tags=['Users'])
class UserViewSet(viewsets.ModelViewSet):
    """
    Manage user profiles for the mobile app.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    # ✅ /api/users/me/  → view or edit own profile
    @extend_schema(
        request=UserSerializer,
        responses={200: UserSerializer},
        examples=[
            OpenApiExample(
                "Profile Update Example",
                value={"first_name": "Ali", "last_name": "Hassan", "show_phone": True},
            )
        ],
    )
    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        user = request.user
        if request.method == 'PATCH':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    # ✅ /api/users/change-password/
    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password changed successfully."),
            400: OpenApiResponse(description="Invalid password or missing data."),
        },
        examples=[
            OpenApiExample(
                "Example",
                value={"old_password": "old123", "new_password": "new456"},
                request_only=True,
            )
        ],
    )
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        user = request.user
        if not user.check_password(old_password):
            return Response({'detail': 'Old password incorrect.'}, status=400)

        user.password = make_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully.'}, status=200)



# -------- Cities
@extend_schema(tags=["Cities"])
class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.filter(is_active=True).order_by("name_en")
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]

# -------- Categories (+ attributes endpoint)
@extend_schema(tags=["Categories"])
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by("name_en")
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        responses={200: AttributeSerializer(many=True)},
        description="List dynamic attributes (with options) for this category."
    )
    @action(detail=True, methods=["get"], url_path="attributes", permission_classes=[permissions.AllowAny])
    def attributes(self, request, pk=None):
        category = self.get_object()
        attrs = Attribute.objects.filter(category=category).prefetch_related("options")
        return Response(AttributeSerializer(attrs, many=True).data)

# -------- Items
@extend_schema(tags=["Items"])
class ItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Public listing = approved + active
        if self.action in ["list", "retrieve"]:
            return (
                Item.objects.filter(is_active=True, is_approved=True)
                .select_related("category", "city")
                .prefetch_related("photos")
                .order_by("-created_at")
            )
        # Owner scoped elsewhere
        return Item.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ItemCreateSerializer
        return ItemListSerializer

    @extend_schema(
        request=ItemCreateSerializer,
        responses={201: ItemListSerializer},
        description="Create a new item. Multipart with photos. Optional JSON 'attributes'."
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        read = ItemListSerializer(item, context={"request": request})
        return Response(read.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={200: ItemListSerializer(many=True)},
        description="List items owned by the current user (any status)."
    )
    @action(detail=False, methods=["get"], url_path="me", permission_classes=[permissions.IsAuthenticated])
    def my_items(self, request):
        qs = (
            Item.objects.filter(user=request.user)
            .select_related("category", "city")
            .prefetch_related("photos")
            .order_by("-created_at")
        )
        return Response(ItemListSerializer(qs, many=True).data)

    @extend_schema(responses={200: OpenApiResponse(description="Item reactivated.")})
    @action(detail=True, methods=["post"], url_path="reactivate", permission_classes=[permissions.IsAuthenticated])
    def reactivate(self, request, pk=None):
        item = get_object_or_404(Item, pk=pk, user=request.user)
        item.is_active = True
        item.save(update_fields=["is_active"])
        return Response({"message": "Item reactivated successfully."})

    @extend_schema(responses={200: OpenApiResponse(description="Item cancelled.")})
    @action(detail=True, methods=["post"], url_path="cancel", permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        item = get_object_or_404(Item, pk=pk, user=request.user)
        item.is_active = False
        item.save(update_fields=["is_active"])
        return Response({"message": "Item cancelled successfully."})

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        if item.user != request.user:
            return Response({"detail": "You do not own this item."}, status=403)
        item.delete()
        return Response({"message": "Item deleted successfully."}, status=200)
