from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings


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