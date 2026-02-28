# marketplace/services/notifications.py
from __future__ import annotations

from marketplace.models import Notification

# -----------------------------
# KINDS (icon/color family)
# -----------------------------
K_REQUEST = "request"
K_AD = "ad"
K_WALLET = "wallet"
K_FAV = "fav"
K_SYSTEM = "system"
K_STORE_FOLLOW = "store_follow"
K_REPORT = "report"

# -----------------------------
# STATUSES (badge)
# -----------------------------

# request / ad
S_PENDING = "pending"
S_APPROVED = "approved"
S_REJECTED = "rejected"
S_FEATURED = "featured"
S_FEATURED_EXPIRED = "featured_expired"

# wallet
S_CHARGED = "charged"
S_USED = "used"
S_REWARD = "reward"

# fav
S_ADDED = "added"

# system
S_INFO = "info"

# store_follow
S_FOLLOWED = "followed"
S_UNFOLLOWED = "unfollowed"

# report
S_SUBMITTED = "submitted"
S_RESOLVED = "resolved"
S_DISMISSED = "dismissed"


def notify(
    *,
    user,
    kind: str = K_SYSTEM,
    status: str = "",
    title: str,
    body: str = "",
    listing=None,
    store=None,
    is_read: bool = False,
):
    """
    Create a notification with a clean, stable shape.
    - kind   : drives icon/color in the frontend
    - status : drives badge label/color in the frontend
    - store  : set for store_follow / store_new_listing notifications so the
               frontend can build the store-profile redirect URL
    - no icon stored in DB
    """
    return Notification.objects.create(
        user=user,
        kind=kind,
        status=status or "",
        title=title,
        body=body or "",
        listing=listing,
        store=store,
        is_read=is_read,
    )


def notify_many(*, users, **kwargs):
    """
    Fan-out helper — sends the same notification to multiple users.
    Useful for report resolution/dismissal where several users
    may have reported the same target.

    Usage:
        notify_many(users=reporters_qs, kind=K_REPORT, status=S_RESOLVED, title="...")
    """
    return [notify(user=user, **kwargs) for user in users]