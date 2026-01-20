from django.db import transaction
from django.utils import timezone

from marketplace.models import ListingPromotion, PromotionEvent, PointsTransaction, User, Listing


class NotEnoughPoints(Exception):
    pass


@transaction.atomic
def buy_featured_with_points(*, user: User, listing: Listing, days: int = 7, points_cost: int = 50) -> ListingPromotion:
    # lock user to prevent double spend
    user = User.objects.select_for_update().get(pk=user.pk)

    print(user.points)
    print(user.phone)
    print(points_cost)
    print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
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
        paid_at=timezone.now(),
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
    promo.activate()
    PromotionEvent.objects.create(
        promotion=promo,
        event="activated",
        meta={"starts_at": promo.starts_at.isoformat(), "ends_at": promo.ends_at.isoformat()},
    )

    return promo
