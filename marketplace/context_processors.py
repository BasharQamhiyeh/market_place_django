from django.db.models import Q
from .models import Notification, Message, Favorite
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
    - recent_messages
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
    # (linked to Listing now)
    # -------------------------
    recent_notifications = (
        Notification.objects.filter(user=user)
        .select_related("listing")
        .order_by("-created_at")[:10]  # ✅ Changed from 6 to 10
    )

    # -------------------------
    # Recent messages
    # (Conversation → Listing)
    # -------------------------
    recent_messages = (
        Message.objects.filter(
            Q(conversation__buyer=user) | Q(conversation__seller=user)
        )
        .select_related(
            "conversation",
            "sender",
            "conversation__listing",
            "conversation__store",
        )
        .order_by("-created_at")[:10]  # ✅ Changed from 6 to 10
    )

    # -------------------------
    # Favorites
    # Favorite → Listing → (Item/Request)
    # -------------------------
    fav_qs = (
        Favorite.objects.filter(user=user)
        .select_related("listing")                  # ✅ Favorite.listing FK
        .prefetch_related("listing__item__photos")  # Item.photos for thumbnail
        .order_by("-created_at")
    )

    favorite_count = fav_qs.count()
    recent_favorites = fav_qs[:5]

    return {
        "unread_notifications": unread_notifications,
        "unread_messages": unread_messages,
        "recent_notifications": recent_notifications,
        "recent_messages": recent_messages,
        "favorite_count": favorite_count,
        "recent_favorites": recent_favorites,
    }


CACHE_VER = "v1"
CACHE_TTL_SECONDS = 60 * 60  # 1 hour


def _pick_name(cat: Category, lang: str) -> str:
    if (lang or "").lower().startswith("ar"):
        return (getattr(cat, "name_ar", "") or "").strip() or (getattr(cat, "name_en", "") or "").strip() or str(cat)
    return (getattr(cat, "name_en", "") or "").strip() or (getattr(cat, "name_ar", "") or "").strip() or str(cat)


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

    order_field = "name_ar" if lang.startswith("ar") else "name_en"

    child_qs = (
        Category.objects
        .only("id", "name_ar", "name_en", "parent_id")
        .order_by(order_field, "id")
    )

    top_qs = (
        Category.objects
        .filter(parent__isnull=True)   # ✅ website categories (top-level)
        .only("id", "name_ar", "name_en")
        .order_by(order_field, "id")
        .prefetch_related(Prefetch("subcategories", queryset=child_qs))
    )

    tree = []
    for top in top_qs:
        children = []
        for ch in top.subcategories.all():
            children.append({
                "id": ch.id,
                "name": _pick_name(ch, lang),
                "url": _pick_url(ch),
            })

        tree.append({
            "id": top.id,
            # "slug": getattr(top, "slug", "") or "",
            "name": _pick_name(top, lang),
            "url": _pick_url(top),
            "children": children,
        })

    cache.set(key, tree, CACHE_TTL_SECONDS)
    return {"navbar_categories": tree}
