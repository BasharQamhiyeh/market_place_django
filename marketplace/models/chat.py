from django.db import models
from django.db.models import Q

from marketplace.models import Listing, User


class Conversation(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True,
    )
    store = models.ForeignKey(
        "marketplace.Store",
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True,
    )

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer_conversations")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller_conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # exactly one target
            models.CheckConstraint(
                check=(
                    (Q(listing__isnull=False) & Q(store__isnull=True)) |
                    (Q(listing__isnull=True) & Q(store__isnull=False))
                ),
                name="conversation_exactly_one_target",
            ),
            # uniqueness for listing conversations
            models.UniqueConstraint(
                fields=["listing", "buyer", "seller"],
                condition=Q(listing__isnull=False),
                name="uniq_convo_listing_buyer_seller",
            ),
            # uniqueness for store conversations
            models.UniqueConstraint(
                fields=["store", "buyer", "seller"],
                condition=Q(store__isnull=False),
                name="uniq_convo_store_buyer_seller",
            ),
        ]

    def __str__(self):
        if self.listing_id:
            return f"Conversation on {self.listing.title}"
        return f"Conversation with store {self.store.name}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender}: {self.body[:20]}"