from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from .models import MobileVerification
from .utils.sms import send_sms_code  # ✅ reuse your existing function

User = get_user_model()


# --------------------------
# 📱 Serializers for Swagger docs
# --------------------------
class ForgotPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(help_text="Phone number for the account")


class VerifyResetSerializer(serializers.Serializer):
    phone = serializers.CharField(help_text="Phone number used during reset")
    code = serializers.CharField(help_text="6-digit verification code")


class ResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(help_text="Phone number used during reset")
    password = serializers.CharField(help_text="New password")


# =====================================================
# Step 1: Request reset code
# =====================================================
@extend_schema(
    request=ForgotPasswordSerializer,
    responses={
        200: OpenApiResponse(description="Reset code sent successfully."),
        400: OpenApiResponse(description="Phone not found or invalid."),
    },
    examples=[
        OpenApiExample(
            "Example Request",
            value={"phone": "+962789999999"},
            request_only=True,
        )
    ],
)
class ForgotPasswordAPI(APIView):
    """
    Step 1: User requests a reset code for password recovery.
    """

    def post(self, request):
        phone = request.data.get("phone")
        if not phone:
            return Response(
                {"detail": "Phone is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(
                {"detail": "Phone number not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = send_sms_code(phone, purpose="reset")

        MobileVerification.objects.update_or_create(
            phone=phone,
            purpose="reset",
            defaults={"code": code, "created_at": timezone.now()},
        )

        return Response(
            {"message": "Reset code sent successfully."},
            status=status.HTTP_200_OK,
        )


# =====================================================
# Step 2: Verify reset code
# =====================================================
@extend_schema(
    request=VerifyResetSerializer,
    responses={
        200: OpenApiResponse(description="Code verified successfully."),
        400: OpenApiResponse(description="Invalid or expired code."),
    },
    examples=[
        OpenApiExample(
            "Example Request",
            value={"phone": "+962789999999", "code": "000000"},
            request_only=True,
        )
    ],
)
class VerifyResetCodeAPI(APIView):
    """
    Step 2: Verify the reset code before allowing password change.
    """

    def post(self, request):
        phone = request.data.get("phone")
        code = request.data.get("code")

        if not all([phone, code]):
            return Response(
                {"detail": "Missing fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            record = MobileVerification.objects.get(phone=phone, purpose="reset")
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

        return Response(
            {"message": "Code verified successfully."},
            status=status.HTTP_200_OK,
        )


# =====================================================
# Step 3: Reset password
# =====================================================
@extend_schema(
    request=ResetPasswordSerializer,
    responses={
        200: OpenApiResponse(description="Password reset successful."),
        400: OpenApiResponse(description="Invalid phone or code not verified."),
    },
    examples=[
        OpenApiExample(
            "Example Request",
            value={"phone": "+962789999999", "password": "newpassword123"},
            request_only=True,
        )
    ],
)
class ResetPasswordAPI(APIView):
    """
    Step 3: Set a new password after verifying reset code.
    """

    def post(self, request):
        phone = request.data.get("phone")
        new_password = request.data.get("password")

        if not all([phone, new_password]):
            return Response(
                {"detail": "Missing fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(
                {"detail": "Phone not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if code was verified recently
        try:
            record = MobileVerification.objects.get(phone=phone, purpose="reset")
        except MobileVerification.DoesNotExist:
            return Response(
                {"detail": "No reset request found or code already used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not record.is_valid():
            return Response(
                {"detail": "Reset code expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Update password
        user.password = make_password(new_password)
        user.save()

        # Delete verification record
        record.delete()

        return Response(
            {"message": "Password reset successful."},
            status=status.HTTP_200_OK,
        )
