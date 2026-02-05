from django.db import transaction
from django.utils import timezone

from marketplace.models import ListingPromotion, PromotionEvent, PointsTransaction, User, Listing


class NotEnoughPoints(Exception):
    pass

class AlreadyFeatured(Exception):
    pass

@transaction.atomic
def buy_featured_with_points(*, user: User, listing: Listing, days: int = 7, points_cost: int = 50) -> ListingPromotion:
    now = timezone.now()

    # lock user to prevent double spend
    user = User.objects.select_for_update().get(pk=user.pk)

    # ✅ lock listing row to prevent concurrent promos
    listing = Listing.objects.select_for_update().get(pk=listing.pk)

    # ✅ expire stale active promos (if any) BEFORE creating a new one
    stale_qs = ListingPromotion.objects.filter(
        listing_id=listing.id,
        kind=ListingPromotion.Kind.FEATURED,
        status=ListingPromotion.Status.ACTIVE,
        ends_at__lte=now,
    )
    if stale_qs.exists():
        stale_qs.update(status=ListingPromotion.Status.EXPIRED, expired_at=now)

    # ✅ block if still active (prevents DB unique constraint crash)
    active_exists = ListingPromotion.objects.filter(
        listing_id=listing.id,
        kind=ListingPromotion.Kind.FEATURED,
        status=ListingPromotion.Status.ACTIVE,
        ends_at__gt=now,
    ).exists()
    if active_exists:
        raise AlreadyFeatured()

    if user.points < points_cost:
        raise NotEnoughPoints()

    promo = ListingPromotion.objects.create(
        listing=listing,
        user=user,
        kind=ListingPromotion.Kind.FEATURED,
        status=ListingPromotion.Status.PENDING,
        duration_days=days,
        points_cost=points_cost,
        paid_with_points=True,
        paid_at=now,
    )
    PromotionEvent.objects.create(promotion=promo, event="created", meta={"points_cost": points_cost, "days": days})

    # deduct points
    user.points -= points_cost
    user.save(update_fields=["points"])

    PointsTransaction.objects.create(
        user=user,
        kind=PointsTransaction.Kind.SPEND,
        delta=-points_cost,
        balance_after=user.points,
        reason="featured_listing",
        ref_promotion=promo,
        meta={"listing_id": listing.id, "listing_type": listing.type, "days": days},
    )
    PromotionEvent.objects.create(promotion=promo, event="points_spent", meta={"points_cost": points_cost})

    # activate (also updates listing.featured_until)
    promo.activate(start=now)

    PromotionEvent.objects.create(
        promotion=promo,
        event="activated",
        meta={"starts_at": promo.starts_at.isoformat(), "ends_at": promo.ends_at.isoformat()},
    )

    return promo


# ✅ NEW: General spend_points function for non-promotion purposes (like republishing)
@transaction.atomic
def spend_points(*, user: User, amount: int, reason: str, meta: dict = None) -> PointsTransaction:
    """
    Deduct points from user for general purposes (republish, etc.)

    Args:
        user: User to deduct points from
        amount: Number of points to deduct (positive integer)
        reason: Reason code (e.g., "republish_listing")
        meta: Optional metadata dict

    Returns:
        PointsTransaction record

    Raises:
        NotEnoughPoints: If user doesn't have enough points
    """
    # lock user to prevent double spend
    user = User.objects.select_for_update().get(pk=user.pk)

    if user.points < amount:
        raise NotEnoughPoints()

    # deduct points
    user.points -= amount
    user.save(update_fields=["points"])

    # create transaction record
    txn = PointsTransaction.objects.create(
        user=user,
        kind=PointsTransaction.Kind.SPEND,
        delta=-amount,
        balance_after=user.points,
        reason=reason,
        ref_promotion=None,  # no promotion for general spending
        meta=meta or {},
    )

    return txn