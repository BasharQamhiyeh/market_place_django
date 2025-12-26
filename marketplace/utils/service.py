from django.db.models import Avg, Count

from marketplace.models import StoreReview, Store


def recalc_store_rating(store_id: int):
    agg = StoreReview.objects.filter(store_id=store_id).aggregate(
        avg=Avg("rating"),
        cnt=Count("id"),
    )
    Store.objects.filter(id=store_id).update(
        rating_avg=agg["avg"] or 0,
        rating_count=agg["cnt"] or 0,
    )
