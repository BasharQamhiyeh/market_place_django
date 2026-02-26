import logging

from django.db import transaction
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Item, Listing, Store, Notification, StoreFollow, ItemPhoto
from . import moderation   # imports the moderation.py you already created
from django.core.cache import cache
from .models import Category

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Item)
def auto_moderate_item(sender, instance: Item, created: bool, **kwargs):
    """
    Run AI moderation on every newly created Item.

    Outcomes:
    - "approve": set is_approved=True so the listing becomes visible.
    - "reject":  keep is_approved=False (default), flag as auto-rejected.
    - "manual":  keep is_approved=False; an admin must review.
    """
    if not created:
        return

    logger.info("Moderating item %s", instance.id)
    decision, reason = moderation.moderate_item(instance)
    logger.info("Moderation result for item %s: %s | %s", instance.id, decision, reason)

    if decision == "approve":
        instance.listing.is_approved = True
        instance.listing.save(update_fields=["is_approved"])

    elif decision == "reject":
        # is_approved is already False (model default); mark as auto-rejected
        instance.listing.is_active = False
        instance.listing.auto_rejected = True
        instance.listing.moderation_reason = reason or "Automatically rejected by AI."
        instance.listing.rejected_at = timezone.now()
        instance.listing.rejected_by = None
        instance.listing.save(
            update_fields=[
                "is_active",
                "auto_rejected",
                "moderation_reason",
                "rejected_at",
                "rejected_by",
            ]
        )

    # "manual": is_approved stays False — admin queue will pick it up


@receiver(pre_save, sender=Listing)
def listing_store_old_state(sender, instance: Listing, **kwargs):
    """
    Save old approval state so we can detect False -> True in post_save.
    """
    if not instance.pk:
        instance._old_is_approved = False
        instance._old_is_active = True
        return

    old = Listing.objects.filter(pk=instance.pk).values("is_approved", "is_active").first() or {}
    instance._old_is_approved = bool(old.get("is_approved", False))
    instance._old_is_active = bool(old.get("is_active", True))


@receiver(post_save, sender=Listing)
def notify_followers_on_approval(sender, instance: Listing, created, **kwargs):
    """
    Notify followers only when:
    - listing becomes approved (False -> True)
    - listing is active
    - not notified before
    """
    old_approved = getattr(instance, "_old_is_approved", False)
    became_approved = (old_approved is False) and (instance.is_approved is True)

    if not became_approved:
        return
    if not instance.is_active:
        return
    if instance.followers_notified:
        return

    # ✅ Get followers (CHANGE THIS QUERY to match your follow table)
    follower_ids = list(
        StoreFollow.objects
        .filter(store__owner_id=instance.user_id)     # store belongs to listing owner
        .values_list("user_id", flat=True)
        .distinct()
    )

    def _create():
        if follower_ids:
            title = "إعلان جديد من متجر تتابعه"
            body = "تم نشر إعلان جديد وتمت الموافقة عليه."

            Notification.objects.bulk_create([
                Notification(
                    user_id=uid,
                    title=title,
                    body=body,
                    listing=instance,
                    is_read=False,
                )
                for uid in follower_ids
            ])

        # ✅ mark as done so it never sends twice
        Listing.objects.filter(pk=instance.pk).update(followers_notified=True)

    transaction.on_commit(_create)


@receiver(post_delete, sender=ItemPhoto)
def delete_itemphoto_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver([post_save, post_delete], sender=Category)
def clear_navbar_categories_cache(sender, instance, **kwargs):
    cache.delete("navbar_cats:v1:en")
    cache.delete("navbar_cats:v1:ar")
