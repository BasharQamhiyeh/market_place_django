from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)

from .models import MobileVerification
from .utils.sms import send_sms_code   # ✅ reuse your existing function

User = get_user_model()


# -------------------------
# 📱 Serializer for Swagger input (phone)
# -------------------------
class PhoneRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(
        help_text="Phone number including country code, e.g. +962789999999"
    )


# -------------------------
# 📱 Serializer for verify step
# -------------------------
class VerifyRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(help_text="Phone number used during registration")
    code = serializers.CharField(help_text="6-digit verification code")
    password = serializers.CharField(help_text="Password for the new account")
    username = serializers.CharField(
        help_text="Optional username (defaults to phone)", required=False
    )


# =====================================================
# Step 1: Request verification code
# =====================================================
@extend_schema(
    request=PhoneRequestSerializer,
    responses={
        200: OpenApiResponse(description="Verification code sent successfully."),
        400: OpenApiResponse(description="Invalid or missing phone."),
    },
    examples=[
        OpenApiExample(
            "Example Request",
            value={"phone": "+962789999999"},
            request_only=True,
        )
    ],
)
class RequestCodeAPI(APIView):
    """
    Step 1: User enters phone, we send verification code.
    """

    def post(self, request):
        phone = request.data.get("phone")
        if not phone:
            return Response(
                {"detail": "Phone is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Generate + send code using your helper
        code = send_sms_code(phone, purpose="verify")

        # ✅ Save or update record in DB
        MobileVerification.objects.update_or_create(
            phone=phone,
            purpose="verify",
            defaults={"code": code, "created_at": timezone.now()},
        )

        return Response(
            {"message": "Verification code sent successfully."},
            status=status.HTTP_200_OK,
        )


# =====================================================
# Step 2: Verify code and create user
# =====================================================
@extend_schema(
    request=VerifyRequestSerializer,
    responses={
        201: OpenApiResponse(description="Registration successful."),
        400: OpenApiResponse(description="Invalid or expired code."),
    },
    examples=[
        OpenApiExample(
            "Example Request",
            value={
                "phone": "+962789999999",
                "code": "000000",
                "password": "mypassword",
                "username": "newuser",
            },
            request_only=True,
        )
    ],
)
class VerifyCodeAPI(APIView):
    """
    Step 2: Verify code and create user (for mobile registration)
    """

    def post(self, request):
        phone = request.data.get("phone")
        code = request.data.get("code")
        password = request.data.get("password")
        username = request.data.get("username") or phone

        if not all([phone, code, password]):
            return Response(
                {"detail": "Missing fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            record = MobileVerification.objects.get(phone=phone, purpose="verify")
        except MobileVerification.DoesNotExist:
            return Response(
                {"detail": "Code not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if record.code != code or not record.is_valid():
            return Response(
                {"detail": "Invalid or expired code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Create or update user
        user, created = User.objects.get_or_create(
            phone=phone, defaults={"username": username}
        )
        user.set_password(password)
        user.phone_verified = True
        user.is_active = True
        user.save()

        # ✅ Delete the verification record
        record.delete()

        # ✅ Auto-login: return JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "phone": user.phone,
                },
                "message": "Registration successful.",
            },
            status=status.HTTP_201_CREATED,
        )
