from django.db import models

from marketplace.models import User, Listing


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