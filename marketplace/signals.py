from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Item
from . import moderation   # imports the moderation.py you already created


@receiver(post_save, sender=Item)
def auto_moderate_item(sender, instance: Item, created: bool, **kwargs):
    """
    When a new item is created, run AI moderation automatically.
    """
    # Only moderate on initial creation
    print("🟡 Signal triggered for item:", instance.id, "created:", created)  # add this

    if not created:
        return

    # Run moderation (calls OpenAI now)
    decision, reason = moderation.moderate_item(instance)

    print("🔵 Moderation decision:", decision, "| reason:", reason)

    # If rejected by AI
    if decision == "reject":
        instance.is_approved = False
        instance.is_active = False
        instance.auto_rejected = True
        instance.moderation_reason = reason or "Automatically rejected by AI."
        instance.cancel_reason = reason or "Automatically rejected by AI."
        instance.rejected_at = timezone.now()
        instance.rejected_by = None  # could later point to a special 'AI Moderator' user
        instance.save(
            update_fields=[
                "is_approved",
                "is_active",
                "auto_rejected",
                "moderation_reason",
                "cancel_reason",
                "rejected_at",
                "rejected_by",
            ]
        )

    # If AI is unsure ("manual"), leave it pending for admin review
