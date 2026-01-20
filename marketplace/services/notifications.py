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

# -----------------------------
# STATUSES (badge)
# -----------------------------
S_PENDING = "pending"
S_APPROVED = "approved"
S_REJECTED = "rejected"
S_FEATURED_EXPIRED = "featured_expired"

S_CHARGED = "charged"
S_USED = "used"
S_REWARD = "reward"

S_ADDED = "added"              # fav
S_INFO = "info"                # system

S_FOLLOWED = "followed"        # store_follow
S_UNFOLLOWED = "unfollowed"    # store_follow


def notify(
    *,
    user,
    kind: str = K_SYSTEM,
    status: str = "",
    title: str,
    body: str = "",
    listing=None,
    is_read: bool = False,
):
    """
    Create notification with clean, stable shape.
    - kind: drives icon/color in frontend
    - status: drives badge label/color in frontend
    - no icon stored in DB
    """
    return Notification.objects.create(
        user=user,
        kind=kind,
        status=status or "",
        title=title,
        body=body or "",
        listing=listing,
        is_read=is_read,
    )
