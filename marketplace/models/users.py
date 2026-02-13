from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
import re
import uuid


def normalize_jo_mobile_to_07(raw: str) -> str:
    """
    Normalize Jordan mobile numbers to local format: 07XXXXXXXX
    Accepts: 07XXXXXXXX, 9627XXXXXXXX, +9627XXXXXXXX, 009627XXXXXXXX, with spaces/dashes.
    """
    if not raw:
        return ""

    digits = re.sub(r"\D+", "", str(raw).strip())

    # 00962... -> 962...
    if digits.startswith("00962"):
        digits = digits[2:]

    # 9627XXXXXXXX -> 07XXXXXXXX
    if digits.startswith("9627") and len(digits) >= 12:
        return "0" + digits[3:13]

    # already 07XXXXXXXX
    if digits.startswith("07") and len(digits) >= 10:
        return digits[:10]

    # edge: 7XXXXXXXX -> 07XXXXXXXX
    if digits.startswith("7") and len(digits) >= 9:
        return "0" + digits[:9]

    return digits

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Users must have a phone number")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password, **extra_fields):
        user = self.create_user(phone=phone, password=password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user



class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    show_phone = models.BooleanField(default=True)

    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="referrals")
    points = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    profile_photo = models.ImageField(upload_to="users/avatars/", blank=True, null=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def save(self, *args, **kwargs):
        # ✅ normalize phone before saving (applies everywhere: admin/forms/api/scripts)
        if self.phone:
            self.phone = normalize_jo_mobile_to_07(self.phone)

        if not self.referral_code:
            self.referral_code = uuid.uuid4().hex[:12]

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.phone}"