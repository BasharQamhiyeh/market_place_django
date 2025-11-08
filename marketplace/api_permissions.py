# marketplace/api_permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.throttling import SimpleRateThrottle


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

class LoginRateThrottle(SimpleRateThrottle):
    """
    Limit login attempts by client IP.
    Scope 'login' uses REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['login'].
    """
    scope = "login"

    def get_cache_key(self, request, view):
        # Use IP address for both authenticated and anonymous attempts
        return self.get_ident(request)