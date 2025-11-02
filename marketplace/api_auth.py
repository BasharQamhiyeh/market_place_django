from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers, permissions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

User = get_user_model()

def normalize(identifier: str) -> str:
    identifier = (identifier or "").strip()
    if identifier.startswith("07") and len(identifier) == 10:
        identifier = "962" + identifier[1:]
    return identifier

class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = normalize(self.initial_data.get("identifier", ""))
        password = self.initial_data.get("password", "")

        user = authenticate(username=identifier, password=password)
        if not user:
            try:
                u = User.objects.get(phone=identifier)
                user = authenticate(username=u.username, password=password)
            except User.DoesNotExist:
                user = None

        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "User inactive."})

        data = super().validate({"username": user.username, "password": password})
        data["user"] = {"user_id": user.user_id, "username": user.username, "phone": getattr(user, "phone", None)}
        return data

class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
