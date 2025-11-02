# marketplace/api_permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """
    Owner can modify; others can read.
    Assumes the object has a `.user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "user_id", None) == getattr(getattr(request, "user", None), "user_id", None)

class IsConversationParticipant(BasePermission):
    def has_object_permission(self, request, view, obj):
        u = getattr(request, "user", None)
        return u and (obj.buyer_id == u.user_id or obj.seller_id == u.user_id)

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

class IsMessageParticipant(BasePermission):
    def has_object_permission(self, request, view, obj):
        u = request.user
        c = obj.conversation
        return u and (c.buyer_id == u.user_id or c.seller_id == u.user_id)

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
