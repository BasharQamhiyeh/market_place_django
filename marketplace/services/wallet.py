# marketplace/services/wallet.py
from django.db import transaction
from django.contrib.auth import get_user_model

from marketplace.models import PointsTransaction


class NotEnoughPoints(Exception):
    pass


@transaction.atomic
def apply_points_transaction(
    *,
    user,
    delta: int,  # signed (+/-)
    kind: str,   # PointsTransaction.Kind.SPEND / EARN / ADJUST
    reason: str = "",
    meta: dict | None = None,
    ref_promotion=None,
    allow_negative: bool = False,
) -> PointsTransaction:
    if delta == 0:
        raise ValueError("delta cannot be 0")

    if meta is None:
        meta = {}

    User = get_user_model()
    u = User.objects.select_for_update().get(pk=user.pk)

    new_balance = int(u.points) + int(delta)
    if (not allow_negative) and new_balance < 0:
        raise NotEnoughPoints()

    u.points = new_balance
    u.save(update_fields=["points"])

    tx = PointsTransaction.objects.create(
        user=u,
        kind=kind,
        delta=int(delta),
        balance_after=new_balance,
        reason=reason or "",
        ref_promotion=ref_promotion,
        meta=meta or {},
    )
    return tx


def earn_points(*, user, amount: int, reason: str = "", meta: dict | None = None, ref_promotion=None):
    if amount <= 0:
        raise ValueError("amount must be > 0")
    return apply_points_transaction(
        user=user,
        delta=+int(amount),
        kind=PointsTransaction.Kind.EARN,
        reason=reason,
        meta=meta,
        ref_promotion=ref_promotion,
    )


def spend_points(*, user, amount: int, reason: str = "", meta: dict | None = None, ref_promotion=None):
    if amount <= 0:
        raise ValueError("amount must be > 0")
    return apply_points_transaction(
        user=user,
        delta=-int(amount),
        kind=PointsTransaction.Kind.SPEND,
        reason=reason,
        meta=meta,
        ref_promotion=ref_promotion,
    )
