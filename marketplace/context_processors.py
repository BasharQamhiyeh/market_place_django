from django.db.models import Q, Max
from .models import Notification, Message, Favorite, Conversation
from django.core.cache import cache
from django.utils import translation
from django.db.models import Prefetch
from .models import Category


def navbar_counters(request):
    """
    Provides counts & recent lists for the top bar:
    - unread_messages
    - unread_notifications
    - favorite_count
    - recent_conversations  (replaces recent_messages)
    - recent_notifications
    - recent_favorites
    """
    if not request.user.is_authenticated:
        return {}

    user = request.user

    # -------------------------
    # Unread notifications
    # -------------------------
    unread_notifications = Notification.objects.filter(
        user=user,
        is_read=False,
    ).count()

    # -------------------------
    # Unread messages
    # (buyer or seller, but not own sent)
    # -------------------------
    unread_messages = (
        Message.objects.filter(
            Q(conversation__buyer=user) | Q(conversation__seller=user),
            is_read=False,
        )
        .exclude(sender=user)
        .count()
    )

    # -------------------------
    # Recent notifications
    # -------------------------
    recent_notifications = (
        Notification.objects.filter(user=user)
        .select_related("listing", "store")
        .order_by("-created_at")[:10]
    )

    # -------------------------
    # Recent CONVERSATIONS (not individual messages)
    # One row per conversation, sorted by latest message date
    # -------------------------
    recent_conversations_qs = (
        Conversation.objects.filter(
            Q(buyer=user) | Q(seller=user)
        )
        .select_related(
            "listing",
            "buyer",
            "buyer__store",
            "seller",
            "seller__store",
        )
        .annotate(latest_msg_date=Max("messages__created_at"))
        .filter(latest_msg_date__isnull=False)  # skip conversations with no messages
        .order_by("-latest_msg_date")[:10]
    )

    # Enrich each conversation with other_user, latest message, and unread flag
    recent_conversations = []
    for conv in recent_conversations_qs:
        other_user = conv.seller if conv.buyer == user else conv.buyer

        latest_msg = conv.messages.order_by("-created_at").first()

        has_unread = (
            conv.messages
            .filter(is_read=False)
            .exclude(sender=user)
            .exists()
        )

        recent_conversations.append({
            "conversation": conv,
            "other_user": other_user,
            "latest_msg": latest_msg,
            "has_unread": has_unread,
        })

    # -------------------------
    # Favorites
    # Favorite → Listing → (Item/Request)
    # -------------------------
    fav_qs = (
        Favorite.objects.filter(user=user, listing__is_deleted=False, listing__is_active=True)
        .select_related("listing", "listing__user__store")
        .prefetch_related("listing__item__photos")
        .order_by("-created_at")
    )

    favorite_count = fav_qs.count()
    recent_favorites = fav_qs[:5]

    return {
        "unread_notifications": unread_notifications,
        "unread_messages": unread_messages,
        "recent_notifications": recent_notifications,
        "recent_conversations": recent_conversations,  # ✅ renamed from recent_messages
        "favorite_count": favorite_count,
        "recent_favorites": recent_favorites,
    }


CACHE_VER = "v1"
CACHE_TTL_SECONDS = 60 * 60  # 1 hour


def _pick_name(cat: Category, lang: str) -> str:
    return (getattr(cat, "name", "") or "").strip()


def _pick_url(cat: Category) -> str:
    fn = getattr(cat, "get_absolute_url", None)
    if callable(fn):
        try:
            return fn()
        except Exception:
            pass
    return f"/category/{cat.id}/"


def navbar_categories(request):
    lang = (translation.get_language() or "en").lower()
    key = f"navbar_cats:{CACHE_VER}:{'ar' if lang.startswith('ar') else 'en'}"

    cached = cache.get(key)
    if cached is not None:
        return {"navbar_categories": cached}

    order_field = "id"

    # Level 3 - grandchildren
    grandchild_qs = (
        Category.objects
        .only("id", "name", "parent_id")
        .order_by(order_field, "id")
    )

    # Level 2 - children with their subcategories prefetched
    child_qs = (
        Category.objects
        .only("id", "name", "parent_id")
        .order_by(order_field, "id")
        .prefetch_related(Prefetch("subcategories", queryset=grandchild_qs))
    )

    # Level 1 - top level
    top_qs = (
        Category.objects
        .filter(parent__isnull=True)
        .only("id", "name")
        .order_by(order_field, "id")
        .prefetch_related(Prefetch("subcategories", queryset=child_qs))
    )

    tree = []
    for top in top_qs:
        children = []
        for ch in top.subcategories.all():
            grandchildren = []
            for gc in ch.subcategories.all():
                grandchildren.append({
                    "id": gc.id,
                    "name": getattr(gc, "name", ""),
                    "url": _pick_url(gc),
                })

            children.append({
                "id": ch.id,
                "name": getattr(ch, "name", ""),
                "url": _pick_url(ch),
                "children": grandchildren,
            })

        tree.append({
            "id": top.id,
            "name": getattr(top, "name", ""),
            "url": _pick_url(top),
            "children": children,
        })

    cache.set(key, tree, CACHE_TTL_SECONDS)

    return {"navbar_categories": tree}