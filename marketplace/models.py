from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_delete
from django.dispatch import receiver

# -----------------------
# Custom User
# -----------------------
class UserManager(BaseUserManager):
    def create_user(self, phone, username, password=None, email=None):
        if not phone:
            raise ValueError("Users must have a phone number")
        user = self.model(phone=phone, username=username, email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, username, password, email=None):
        user = self.create_user(phone=phone, username=username, password=password, email=email)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    show_phone = models.BooleanField(
        default=True,
        help_text="If true, your phone number will be visible to other users."
    )

    # NEW FIELDS
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals"
    )
    points = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone"]

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = uuid.uuid4().hex[:12]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.first_name or ''} {self.last_name or ''})".strip()



# -----------------------
# Categories and Attributes
# -----------------------
class Category(models.Model):
    name_en = models.CharField(max_length=255, unique=True)
    name_ar = models.CharField(max_length=255, unique=True)
    subtitle_en = models.CharField(max_length=255, blank=True, null=True)
    subtitle_ar = models.CharField(max_length=255, blank=True, null=True)
    icon = models.CharField(
        max_length=50,  # 👈 IMPORTANT: keep it 50 (NOT 10)
        blank=True,
        null=True,
        help_text="Choose an emoji icon for this category"
    )

    # 🧩 Icon color (text field — admin can pick or type a color)
    color = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Emoji color (optional)"
    )
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subcategories",
        null=True,
        blank=True
    )

    def __str__(self):
        from django.utils import translation
        lang = translation.get_language()
        return self.name_ar if lang == 'ar' else self.name_en

    class Meta:
        verbose_name_plural = "Categories"




class Attribute(models.Model):
    INPUT_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('select', 'Select'),
    ]
    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255)
    input_type = models.CharField(max_length=50, choices=INPUT_TYPE_CHOICES, default='text')
    is_required = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="attributes")

    def __str__(self):
        from django.utils import translation
        lang = translation.get_language()
        return self.name_ar if lang == 'ar' else self.name_en



class AttributeOption(models.Model):
    value_en = models.CharField(max_length=255)
    value_ar = models.CharField(max_length=255)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="options")

    def __str__(self):
        from django.utils import translation
        lang = translation.get_language()
        return self.value_ar if lang == 'ar' else self.value_en



# -----------------------
# Items and related tables
# -----------------------
class Item(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
    ]

    title = models.TextField()
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='items')
    description = models.TextField(blank=True)
    price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='items')

    sold_on_site = models.BooleanField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True, null=True)

    # moderation/state
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    was_edited = models.BooleanField(default=False)

    # ✅ NEW
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used')

    # ✅ NEW: external id coming from Excel sheet (used to match photos in later ZIP uploads)
    external_id = models.CharField(max_length=64, null=True, blank=True, unique=True, db_index=True)

    # ✅ NEW: track who approved/rejected (+ optional timestamps)
    approved_by = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_items')
    rejected_by = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL, related_name='rejected_items')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    auto_rejected = models.BooleanField(default=False)  # True if AI did the rejection
    moderation_reason = models.TextField(blank=True, null=True)  # why AI rejected it

    @property
    def main_photo(self):
        """Return the preferred (is_main) photo, or first one."""
        return self.photos.filter(is_main=True).first() or self.photos.first()

    def __str__(self):
        return self.title



class ItemPhoto(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='items/')
    created_at = models.DateTimeField(auto_now_add=True)
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"Photo for {self.item.title}"


class ItemAttributeValue(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='attribute_values')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.attribute.name_en}/{self.attribute.name_ar}: {self.value}"

    # TODO: see why chatgpt changed it to this ?
    # def __str__(self):
    #     # safe label
    #     try:
    #         from django.utils import translation
    #         return f"{self.attribute.name_ar if translation.get_language() == 'ar' else self.attribute.name_en}: {self.value}"
    #     except Exception:
    #         return f"{self.attribute_id}: {self.value}"



class Conversation(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="conversations")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer_conversations")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller_conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation on {self.item.title} between {self.buyer} and {self.seller}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # 👈 add this field


    def __str__(self):
        return f"From {self.sender}: {self.body[:20]}"


class Notification(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    item = models.ForeignKey('Item', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.title}"


class City(models.Model):
    name_en = models.CharField(max_length=150, unique=True)
    name_ar = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ["name_en"]

    def __str__(self):
        from django.utils import translation
        lang = translation.get_language()
        return self.name_ar if lang == "ar" else self.name_en


# -----------------------
# Favorites (Wishlist)
# -----------------------
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "item")
        indexes = [
            models.Index(fields=["user", "item"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.item.title}"


from datetime import timedelta, datetime
from django.utils import timezone

class PhoneVerificationCode(models.Model):
    PURPOSE_CHOICES = [
        ('verify', 'Phone Verification'),
        ('reset', 'Password Reset'),
    ]
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        """Code is valid for 10 minutes."""
        return timezone.now() < self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.phone} → {self.code} ({self.purpose})"


# models.py
class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class IssueReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=[("open", "Open"), ("resolved", "Resolved")], default="open")
    created_at = models.DateTimeField(auto_now_add=True)


class PhoneVerification(models.Model):
    phone = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.created_at >= timezone.now() - timedelta(minutes=5)


class MobileVerification(models.Model):
    PURPOSE_CHOICES = [
        ("verify", "Phone Verification"),
        ("reset", "Password Reset"),
    ]

    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        """Code is valid for 5 minutes"""
        return self.created_at >= timezone.now() - timedelta(minutes=5)

    def __str__(self):
        return f"{self.phone} ({self.purpose})"


@receiver(post_delete, sender=ItemPhoto)
def delete_itemphoto_file(sender, instance, **kwargs):
    """
    Delete image file from storage (local or Cloudinary) when ItemPhoto is deleted.
    This runs automatically after an Item or ItemPhoto is deleted.
    """
    if instance.image:
        instance.image.delete(save=False)