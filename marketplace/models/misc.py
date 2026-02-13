from django.db import models, transaction
from django.utils import timezone
from marketplace.models import User
from django.core.exceptions import ValidationError
from datetime import timedelta


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