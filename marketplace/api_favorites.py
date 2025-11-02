from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Item, Favorite
from .serializers import ItemSerializer

User = get_user_model()


@extend_schema(tags=["Favorites"])
class FavoriteViewSet(viewsets.ViewSet):
    """
    Manage user favorites for the mobile API.
    """

    permission_classes = [permissions.IsAuthenticated]

    # ----------------------------------------
    # ✅ GET /api/me/favorites/
    # ----------------------------------------
    @extend_schema(
        responses={200: ItemSerializer(many=True)},
        description="List all items favorited by the current user.",
    )
    @action(detail=False, methods=["get"], url_path="me/favorites")
    def list_favorites(self, request):
        favorites = Favorite.objects.filter(user=request.user).select_related("item", "item__category", "item__city")
        items = [fav.item for fav in favorites]
        serializer = ItemSerializer(items, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ----------------------------------------
    # ✅ POST /api/items/{id}/favorite/
    # ----------------------------------------
    @extend_schema(
        responses={
            200: OpenApiResponse(description="Favorite toggled successfully."),
            404: OpenApiResponse(description="Item not found."),
        },
        examples=[
            OpenApiExample("Toggle favorite", value={"message": "Added to favorites."})
        ],
    )
    @action(detail=True, methods=["post"], url_path="favorite")
    def toggle_favorite(self, request, pk=None):
        item = get_object_or_404(Item, pk=pk)
        fav, created = Favorite.objects.get_or_create(user=request.user, item=item)
        if not created:
            fav.delete()
            return Response({"message": "Removed from favorites."}, status=status.HTTP_200_OK)
        return Response({"message": "Added to favorites."}, status=status.HTTP_200_OK)
