from django.core.management.base import BaseCommand
from django.utils import timezone

from marketplace.models import Listing, ListingPromotion
from marketplace.services.notifications import (
    notify,
    K_AD,
    K_REQUEST,
    S_FEATURED_EXPIRED,
)


class Command(BaseCommand):
    help = "Expire featured listings and notify owners. Run every 12 hours via cron."

    def handle(self, *args, **options):
        now = timezone.now()
        count = 0

        # ------------------------------------------------------------------
        # 1. Normal flow — listings that have a ListingPromotion record
        # ------------------------------------------------------------------
        expired_promos = (
            ListingPromotion.objects.filter(
                status=ListingPromotion.Status.ACTIVE,
                ends_at__lt=now,
            )
            .select_related("listing", "listing__user")
        )

        for promo in expired_promos:
            listing = promo.listing

            # Skip if we already notified for this expiry cycle
            if (
                listing.featured_expired_notified_at
                and listing.featured_expired_notified_at >= promo.ends_at
            ):
                continue

            # Mark promotion as expired
            promo.status = ListingPromotion.Status.EXPIRED
            promo.expired_at = now
            promo.save(update_fields=["status", "expired_at"])

            # Clear listing featured cache and mark notified
            listing.featured_until = None
            listing.featured_expired_notified_at = now
            listing.save(update_fields=["featured_until", "featured_expired_notified_at"])

            self._notify(listing)
            count += 1

            self.stdout.write(f"  → Expired promo #{promo.id} for listing #{listing.id} ({listing.title})")

        # ------------------------------------------------------------------
        # 2. Fallback — orphan listings with featured_until expired
        #    but no ListingPromotion record (e.g. set manually via old admin)
        # ------------------------------------------------------------------
        orphan_listings = (
            Listing.objects.filter(
                featured_until__lt=now,
                featured_until__isnull=False,
                featured_expired_notified_at__isnull=True,
            )
            .exclude(promotions__status=ListingPromotion.Status.ACTIVE)
            .select_related("user")
        )

        for listing in orphan_listings:
            listing.featured_until = None
            listing.featured_expired_notified_at = now
            listing.save(update_fields=["featured_until", "featured_expired_notified_at"])

            self._notify(listing)
            count += 1

            self.stdout.write(f"  → Expired orphan listing #{listing.id} ({listing.title})")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Done. Expired {count} featured listing(s) and notified owners."))

    def _notify(self, listing):
        kind = K_AD if listing.type == "item" else K_REQUEST
        title = (
            "انتهت فترة تمييز إعلانك"
            if listing.type == "item"
            else "انتهت فترة تمييز طلبك"
        )
        notify(
            user=listing.user,
            kind=kind,
            status=S_FEATURED_EXPIRED,
            title=title,
            body=f"انتهت فترة تمييز \"{listing.title}\".",
            listing=listing,
        )