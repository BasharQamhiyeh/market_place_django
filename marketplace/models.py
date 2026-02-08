from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import uuid
from PIL import Image, ImageOps, ImageFilter
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, F
import re

from django.utils.text import slugify


# ======================================================
# CITY
# ======================================================

class City(models.Model):
    name_en = models.CharField(max_length=150, unique=True)
    name_ar = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ["name_en"]

    def __str__(self):
        from django.utils import translation
        return self.name_ar if translation.get_language() == "ar" else self.name_en



# ======================================================
# USER
# ======================================================

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


# ======================================================
# STORE (NO SLUG)
# ======================================================
class Store(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="store",
    )

    # BASIC
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # MEDIA
    logo = models.ImageField(upload_to="stores/logos/", blank=True, null=True)
    cover = models.ImageField(upload_to="stores/covers/", blank=True, null=True)

    # CONTACT
    whatsapp = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)

    # LOCATION
    city = models.ForeignKey(
        "marketplace.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stores",
    )

    address = models.CharField(max_length=255, blank=True)

    # STATUS
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # mockup
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # cached rating
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    specialty = models.CharField(max_length=100, blank=True)  # تخصص المتجر (optional in DB)
    show_phone = models.BooleanField(default=True)  # إعدادات عرض رقم الهاتف

    # store payment methods: ["cash","card","cliq","transfer"]
    payment_methods = models.JSONField(default=list, blank=True)

    DELIVERY_CHOICES = [
        ("24", "خلال 24 ساعة"),
        ("48", "خلال 48 ساعة"),
        ("72", "خلال 72 ساعة"),
    ]
    delivery_policy = models.CharField(max_length=2, choices=DELIVERY_CHOICES, blank=True)

    RETURN_CHOICES = [
        ("3", "خلال 3 أيام"),
        ("7", "خلال 7 أيام"),
        ("none", "لا يوجد إرجاع"),
    ]
    return_policy = models.CharField(max_length=10, choices=RETURN_CHOICES, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "created_at"]),
        ]

    def __str__(self):
        return self.name

    @property
    def logo_url(self):
        return self.logo.url if self.logo else "/static/img/default-store.png"


# ======================================================
# STORE FOLLOW (NEW)
# ======================================================
class StoreFollow(models.Model):
    store = models.ForeignKey(
        "marketplace.Store",
        on_delete=models.CASCADE,
        related_name="followers",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_stores",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["store", "user"], name="uniq_store_follow")
        ]
        indexes = [
            models.Index(fields=["store", "user"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} follows store {self.store_id}"


# ======================================================
# STORE REVIEW (UPDATED)
# ======================================================
class StoreReview(models.Model):
    store = models.ForeignKey(
        "marketplace.Store",
        on_delete=models.CASCADE,
        related_name="reviews",
        db_index=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="store_reviews_made",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    subject = models.CharField(max_length=120, blank=True)
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "reviewer"],
                name="uniq_store_reviewer_review",
            )
        ]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "-created_at"]),
            models.Index(fields=["reviewer", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.store_id} - {self.reviewer_id} - {self.rating}"

# ======================================================
# CATEGORY + ATTRIBUTE MODEL SYSTEM
# ======================================================

class Category(models.Model):
    name_en = models.CharField(max_length=255, unique=True)
    name_ar = models.CharField(max_length=255, unique=True)
    child_label = models.CharField(max_length=255, blank=True, null=True)
    subtitle_en = models.CharField(max_length=255, blank=True, null=True)
    subtitle_ar = models.CharField(max_length=255, blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="subcategories", null=True, blank=True)

    @property
    def photo_url(self):
        p = getattr(self, "photo", None)
        if p and getattr(p, "image", None):
            try:
                return p.image.url
            except Exception:
                return None
        return None

    def __str__(self):
        from django.utils import translation
        return self.name_ar if translation.get_language() == "ar" else self.name_en

    class Meta:
        verbose_name_plural = "Categories"


class CategoryPhoto(models.Model):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name="photo")
    image = models.ImageField(upload_to="categories/")  # ✅ uses your configured storage
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.category.name_ar}"


class Attribute(models.Model):
    INPUT_TYPE_CHOICES = [('text', 'Text'), ('number', 'Number'), ('select', 'Select')]
    UI_TYPE_CHOICES = [
        ('dropdown', 'Dropdown'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox List'),
        ('single_checkbox', 'Single Checkbox'),
        ('tags', 'Tags / Multi-Select'),
    ]

    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255)
    input_type = models.CharField(max_length=50, choices=INPUT_TYPE_CHOICES, default='text')
    ui_type = models.CharField(max_length=50, choices=UI_TYPE_CHOICES, default='dropdown')
    is_required = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="attributes")

    def __str__(self):
        from django.utils import translation
        return self.name_ar if translation.get_language() == 'ar' else self.name_en


class AttributeOption(models.Model):
    value_en = models.CharField(max_length=255)
    value_ar = models.CharField(max_length=255)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="options")

    def __str__(self):
        from django.utils import translation
        return self.value_ar if translation.get_language() == 'ar' else self.value_en


# ======================================================
# LISTING (Parent for ITEM + REQUEST)
# ======================================================

class Listing(models.Model):
    TYPE_CHOICES = [
        ('item', 'Item'),
        ('request', 'Request'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="listings")
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, related_name="listings")

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)    # same moderation workflow
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    published_at = models.DateTimeField(default=timezone.now, db_index=True)

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_listings"
    )
    rejected_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="rejected_listings"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    auto_rejected = models.BooleanField(default=False)
    moderation_reason = models.TextField(blank=True, null=True)

    show_phone = models.BooleanField(default=True)  # ✅ add this

    featured_until = models.DateTimeField(null=True, blank=True, db_index=True)

    followers_notified = models.BooleanField(default=False)

    views_count = models.PositiveIntegerField(default=0, db_index=True)

    @property
    def is_featured(self):
        until = self.featured_until
        return bool(until and until > timezone.now())

    def __str__(self):
        return f"{self.title} ({self.type})"


class ListingPromotion(models.Model):
    class Kind(models.TextChoices):
        FEATURED = "featured", "Featured"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        CANCELED = "canceled", "Canceled"
        FAILED = "failed", "Failed"

    listing = models.ForeignKey("marketplace.Listing", on_delete=models.CASCADE, related_name="promotions")
    user = models.ForeignKey("marketplace.User", on_delete=models.CASCADE, related_name="listing_promotions")

    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.FEATURED)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    duration_days = models.PositiveIntegerField(default=7)

    # ✅ points-based payment
    points_cost = models.PositiveIntegerField(default=0)
    paid_with_points = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["kind", "status", "ends_at"]),
            models.Index(fields=["listing", "kind"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(starts_at__isnull=True, ends_at__isnull=True) | Q(ends_at__gt=F("starts_at")),
                name="promo_ends_after_starts",
            ),
            models.UniqueConstraint(
                fields=["listing", "kind"],
                condition=Q(status="active"),
                name="uniq_active_promo_per_listing_kind",
            ),
        ]

    def activate(self, *, start=None):
        """
        Activates this promotion and updates listing.featured_until cache.

        NOTE: The actual points deduction must happen OUTSIDE (in a service/view),
        then call activate().
        """
        now = timezone.now()
        start = start or now

        with transaction.atomic():
            # lock listing row to avoid race conditions
            listing = self.listing.__class__.objects.select_for_update().get(pk=self.listing_id)

            # stacking: if already active featured exists, start after it
            active = ListingPromotion.objects.filter(
                listing_id=self.listing_id,
                kind=self.kind,
                status=self.Status.ACTIVE,
                ends_at__gt=now,
            ).order_by("-ends_at").first()

            if active and active.ends_at:
                start = max(active.ends_at, now)

            ends = start + timezone.timedelta(days=self.duration_days)

            self.starts_at = start
            self.ends_at = ends
            self.status = self.Status.ACTIVE
            self.activated_at = now
            self.save(update_fields=["starts_at", "ends_at", "status", "activated_at"])

            # update Listing cache
            listing.featured_until = max(listing.featured_until or now, ends)
            listing.save(update_fields=["featured_until"])


class PromotionEvent(models.Model):
    promotion = models.ForeignKey("marketplace.ListingPromotion", on_delete=models.CASCADE, related_name="events")
    event = models.CharField(max_length=40)  # created, points_spent, activated, expired...
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["event", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event} for promo #{self.promotion_id}"


class PointsTransaction(models.Model):
    class Kind(models.TextChoices):
        SPEND = "spend", "Spend"
        EARN = "earn", "Earn"
        ADJUST = "adjust", "Adjust"

    user = models.ForeignKey("marketplace.User", on_delete=models.CASCADE, related_name="points_transactions")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    delta = models.IntegerField()  # negative for spend, positive for earn
    balance_after = models.IntegerField()
    reason = models.CharField(max_length=80, blank=True, default="")  # e.g. "featured_listing"
    ref_promotion = models.ForeignKey(
        "marketplace.ListingPromotion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="points_transactions",
    )
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.user_id} {self.kind} {self.delta}"

# ======================================================
# ITEM (child of Listing)
# ======================================================

class Item(models.Model):
    CONDITION_CHOICES = [('new', 'New'), ('used', 'Used')]

    listing = models.OneToOneField("Listing", on_delete=models.CASCADE, related_name="item")

    price = models.FloatField()
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used')

    sold_on_site = models.BooleanField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True, null=True)

    external_id = models.CharField(max_length=64, null=True, blank=True, unique=True, db_index=True)

    auto_rejected = models.BooleanField(default=False)
    moderation_reason = models.TextField(blank=True, null=True)

    @property
    def main_photo(self):
        main = self.photos.filter(is_main=True).first()
        return main or self.photos.order_by('id').first()

    def __str__(self):
        return self.listing.title


# Single normalized target (16:10)
NORMAL_W = 1600
NORMAL_H = 1000


class ItemPhoto(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='items/')  # original
    normalized = models.ImageField(upload_to='items/normalized/', blank=True, null=True)  # ✅ single normalized
    created_at = models.DateTimeField(auto_now_add=True)
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"Photo for {self.item.listing.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # generate once (or regenerate if original changed and normalized missing)
        if self.image and not self.normalized:
            self.generate_normalized()

    def generate_normalized(self):
        """
        Create a single normalized image:
        - exact size NORMAL_W x NORMAL_H
        - FULL image visible (no crop)
        - no empty space (filled with blurred background)
        """
        try:
            # open from storage
            self.image.open("rb")
            im = Image.open(self.image)
            im = ImageOps.exif_transpose(im)  # fix rotation from phone photos
            im = im.convert("RGB")

            # background: cover then blur (fills full canvas)
            bg = ImageOps.fit(im, (NORMAL_W, NORMAL_H), method=Image.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(28))

            # foreground: contain (no crop)
            fg = ImageOps.contain(im, (NORMAL_W, NORMAL_H), method=Image.LANCZOS)

            # paste centered
            x = (NORMAL_W - fg.width) // 2
            y = (NORMAL_H - fg.height) // 2
            bg.paste(fg, (x, y))

            # write to buffer
            buf = BytesIO()
            bg.save(buf, format="JPEG", quality=85, optimize=True, progressive=True)

            base = self.image.name.split("/")[-1]
            name = f"norm_{base.rsplit('.', 1)[0]}.jpg"

            self.normalized.save(name, ContentFile(buf.getvalue()), save=False)
            super().save(update_fields=["normalized"])

        except Exception as e:
            print("Normalized image generation failed:", e)
        finally:
            try:
                self.image.close()
            except Exception:
                pass


class ItemAttributeValue(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='attribute_values')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.attribute}: {self.value}"


# ======================================================
# REQUEST (child of Listing)
# ======================================================

class Request(models.Model):
    CONDITION_CHOICES = [
        ("any", "لا يهم"),
        ("new", "جديد"),
        ("used", "مستعمل"),
    ]

    listing = models.OneToOneField(Listing, on_delete=models.CASCADE, related_name="request")

    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition_preference = models.CharField(max_length=10, choices=CONDITION_CHOICES, default="any")

    def __str__(self):
        return self.listing.title


class RequestAttributeValue(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.attribute} = {self.value or '(no preference)'}"



# ======================================================
# CONVERSATION / MESSAGE (now linked to Listing)
# ======================================================

class Conversation(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True,
    )
    store = models.ForeignKey(
        "marketplace.Store",
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True,
    )

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer_conversations")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller_conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # exactly one target
            models.CheckConstraint(
                check=(
                    (Q(listing__isnull=False) & Q(store__isnull=True)) |
                    (Q(listing__isnull=True) & Q(store__isnull=False))
                ),
                name="conversation_exactly_one_target",
            ),
            # uniqueness for listing conversations
            models.UniqueConstraint(
                fields=["listing", "buyer", "seller"],
                condition=Q(listing__isnull=False),
                name="uniq_convo_listing_buyer_seller",
            ),
            # uniqueness for store conversations
            models.UniqueConstraint(
                fields=["store", "buyer", "seller"],
                condition=Q(store__isnull=False),
                name="uniq_convo_store_buyer_seller",
            ),
        ]

    def __str__(self):
        if self.listing_id:
            return f"Conversation on {self.listing.title}"
        return f"Conversation with store {self.store.name}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender}: {self.body[:20]}"


# ======================================================
# FAVORITES (now linked to Listing)
# ======================================================

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "listing")
        indexes = [
            models.Index(fields=["user", "listing"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.listing.title}"


# ======================================================
# NOTIFICATIONS (now linked to Listing)
# ======================================================

# marketplace/models.py

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")

    # group for icon/color family (request/ad/wallet/fav/system/store_follow)
    kind = models.CharField(max_length=30, default="system", db_index=True)

    # badge/status near title (pending/approved/rejected/featured_expired/charged/used/reward/...)
    status = models.CharField(max_length=30, blank=True, default="", db_index=True)

    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)

    # optional link target
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"{self.user} - {self.kind}:{self.status} - {self.title}"




# ======================================================
# SUBSCRIBER / ISSUE REPORT / VERIFICATION
# ======================================================

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class IssuesReport(models.Model):
    TARGET_KINDS = [
        ("listing", "Listing"),
        ("user", "User"),
        ("store", "Store"),
    ]

    LISTING_TYPES = [
        ("item", "Item"),
        ("request", "Request"),
    ]


    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports_made")
    target_kind = models.CharField(max_length=10, choices=TARGET_KINDS, db_index=True)

    # Targets (only one should be set)
    listing = models.ForeignKey("marketplace.Listing", null=True, blank=True, on_delete=models.CASCADE, related_name="reports")
    reported_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="reports_received")
    store = models.ForeignKey("marketplace.Store", null=True, blank=True, on_delete=models.CASCADE, related_name="reports")

    # For listing filtering (only relevant when target_kind="listing")
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPES, null=True, blank=True, db_index=True)

    reason = models.CharField(max_length=100, blank=True, db_index=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[("open", "Open"), ("resolved", "Resolved")],
        default="open",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Enforce exactly one target is set, matching target_kind
        targets = {
            "listing": self.listing_id is not None,
            "user": self.reported_user_id is not None,
            "store": self.store_id is not None,
        }

        if self.target_kind not in targets:
            raise ValidationError({"target_kind": "Invalid target_kind."})

        # exactly one target overall
        if sum(bool(v) for v in targets.values()) != 1:
            raise ValidationError("Exactly one target (listing/user/store) must be set.")

        # the chosen target_kind must match the filled FK
        if not targets[self.target_kind]:
            raise ValidationError("target_kind does not match the provided target.")

        # listing_type required only for listing reports
        if self.target_kind == "listing":
            if self.listing_type not in ("item", "request"):
                raise ValidationError({"listing_type": "listing_type is required for listing reports."})
        else:
            # not listing -> listing_type must be empty
            if self.listing_type:
                raise ValidationError({"listing_type": "listing_type must be empty unless target_kind='listing'."})

    class Meta:
        indexes = [
            models.Index(fields=["target_kind", "status", "created_at"]),
            models.Index(fields=["listing_type", "status", "created_at"]),
        ]


class PhoneVerificationCode(models.Model):
    PURPOSE_CHOICES = [
        ('verify', 'Phone Verification'),
        ('reset', 'Password Reset'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=10)


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
        return self.created_at >= timezone.now() - timedelta(minutes=5)


# ======================================================
# DELETE FILES FOR ITEM PHOTOS
# ======================================================

@receiver(post_delete, sender=ItemPhoto)
def delete_itemphoto_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ("account", "مشكلة حساب"),
        ("suggestion", "اقتراح"),
        ("complaint", "شكوى"),
        ("other", "أخرى"),
    ]

    METHOD_CHOICES = [
        ("phone", "رقم الهاتف"),
        ("email", "البريد الإلكتروني"),
    ]

    full_name = models.CharField(max_length=200)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)

    contact_method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # optional: admin workflow
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.get_subject_display()} - {self.created_at:%Y-%m-%d}"


class FAQCategory(models.Model):
    """
    Represents a section/type in the FAQ page (about, account, ads, requests, safety, issues).
    """
    key = models.SlugField(
        max_length=32,
        unique=True,
        help_text="Unique key used in template anchors. Example: about, account, ads..."
    )
    name_ar = models.CharField(max_length=120)
    icon = models.CharField(
        max_length=40,
        blank=True,
        default="circle-help",
        help_text="Lucide icon name, e.g. info, user-cog, megaphone..."
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    @property
    def active_questions(self):
        # if you have related_name="questions" use that, otherwise use faqquestion_set
        rel = getattr(self, "questions", None)
        if rel is None:
            rel = self.faqquestion_set
        return rel.filter(is_active=True).order_by("order", "id")

    def __str__(self) -> str:
        return self.name_ar


class FAQQuestion(models.Model):
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name="questions")
    question_ar = models.CharField(max_length=255)
    answer_ar = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__order", "order", "id"]

    def __str__(self) -> str:
        return f"{self.category.key}: {self.question_ar[:60]}"



class PrivacyPolicyPage(models.Model):
    """
    صفحة سياسة الخصوصية (نسخ Versioning).
    نخلي نسخة واحدة Active فقط، والأدمن يقدر ينشئ نسخة جديدة ويخليها Active.
    """
    title_ar = models.CharField(max_length=200, default="سياسة الخصوصية")
    subtitle_ar = models.CharField(
        max_length=300,
        blank=True,
        default="نوضح هنا كيف نجمع بياناتك ونستخدمها ونحميها داخل منصة ركن."
    )

    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "-published_at"]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.is_active:
                PrivacyPolicyPage.objects.exclude(pk=self.pk).update(is_active=False)


    def __str__(self) -> str:
        status = "ACTIVE" if self.is_active else "draft"
        return f"{self.title_ar} ({status})"


class PrivacyPolicySection(models.Model):
    page = models.ForeignKey(
        PrivacyPolicyPage,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    order = models.PositiveIntegerField(default=1)

    heading_ar = models.CharField(max_length=200)
    body_ar = models.TextField(help_text="اكتب النص العربي (يمكنك استخدام أسطر جديدة).")

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.order}. {self.heading_ar}"



