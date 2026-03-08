from django.db import models
from django.utils import timezone

from marketplace.models.users import User
from marketplace.models.city import City


class Report(models.Model):
    TYPE_LOST = 'lost'
    TYPE_FOUND = 'found'
    TYPE_CHOICES = [
        (TYPE_LOST, 'Lost'),
        (TYPE_FOUND, 'Found'),
    ]

    CAT_OFFICIAL_DOCS = 'official_docs'
    CAT_PERSONAL = 'personal'
    CAT_DEVICES = 'devices'
    CAT_PETS = 'pets'
    CAT_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CAT_OFFICIAL_DOCS, 'أوراق رسمية'),
        (CAT_PERSONAL, 'مقتنيات شخصية'),
        (CAT_DEVICES, 'أجهزة'),
        (CAT_PETS, 'حيوانات أليفة'),
        (CAT_OTHER, 'أخرى'),
    ]

    CONTACT_PHONE = 'phone'
    CONTACT_MESSAGE = 'message'
    CONTACT_TYPE_CHOICES = [
        (CONTACT_PHONE, 'موبايل'),
        (CONTACT_MESSAGE, 'رسائل داخل الموقع'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    area = models.CharField(max_length=255, blank=True)

    incident_date = models.DateField(null=True, blank=True)

    show_phone = models.BooleanField(default=True)
    contact_type = models.CharField(max_length=10, choices=CONTACT_TYPE_CHOICES, default=CONTACT_PHONE)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)

    # Moderation fields
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_reports'
    )
    rejected_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='rejected_reports'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_display()}] {self.title}"

    @property
    def main_photo(self):
        return self.photos.filter(is_main=True).first() or self.photos.order_by('id').first()


class ReportPhoto(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='lost_found/')
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for report {self.report_id}"


class ReportMatch(models.Model):
    """
    Stores a match between a lost report and a found report.
    Prevents duplicate notifications.
    """
    lost_report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name='matches_as_lost'
    )
    found_report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name='matches_as_found'
    )
    score = models.PositiveSmallIntegerField(default=0)
    lost_notified = models.BooleanField(default=False)
    found_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lost_report', 'found_report')
        ordering = ['-score', '-created_at']

    def __str__(self):
        return f"Match: lost#{self.lost_report_id} <-> found#{self.found_report_id} (score={self.score})"
