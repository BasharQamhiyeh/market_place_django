from django.db import models, transaction
from django.db.models import Q, F
from django.utils import timezone

from marketplace.models import User, Category


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