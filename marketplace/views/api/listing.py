import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages

from marketplace.models import Listing, Item, Favorite
from marketplace.services.notifications import notify, K_WALLET, S_USED, K_FAV, S_ADDED
from marketplace.views.constants import FEATURE_PACKAGES
from marketplace.services.promotions import buy_featured_with_points, spend_points, NotEnoughPoints, AlreadyFeatured

@login_required
@require_POST
def feature_listing_api(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id, user=request.user)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    days = int(payload.get("days", 0))
    if days not in FEATURE_PACKAGES:
        return JsonResponse({"ok": False, "error": "invalid_days"}, status=400)

    # mockup disables if still featured
    if listing.featured_until and listing.featured_until > timezone.now():
        return JsonResponse({"ok": False, "error": "already_featured"}, status=400)

    cost = FEATURE_PACKAGES[days]

    try:
        promo = buy_featured_with_points(
            user=request.user,
            listing=listing,
            days=days,
            points_cost=cost,
        )
    except NotEnoughPoints:
        return JsonResponse({"ok": False, "error": "not_enough_points"}, status=400)
    except AlreadyFeatured:
        return JsonResponse({"ok": False, "error": "already_featured"}, status=400)

    # refresh listing cache updated by promo.activate()
    listing.refresh_from_db(fields=["featured_until"])
    request.user.refresh_from_db(fields=["points"])

    notify(
        user=request.user,
        kind=K_WALLET,
        status=S_USED,
        title="تم خصم نقاط",
        body=f"تم خصم {cost} نقطة مقابل تمييز \"{listing.title}\" لمدة {days} أيام.",
        listing=listing,
    )

    return JsonResponse({
        "ok": True,
        "days": days,
        "cost": cost,
        "points_balance": request.user.points,
        "featured_until": listing.featured_until.isoformat() if listing.featured_until else None,
        "promotion_id": promo.id,
    })


@login_required
@require_POST
def delete_listing_api(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id, user=request.user)

    # already deleted => idempotent
    if getattr(listing, "is_deleted", False):
        return JsonResponse({"ok": True, "already": True})

    listing.is_deleted = True
    listing.is_active = False  # مهم: ما يرجع يظهر بأي مكان
    if hasattr(listing, "deleted_at"):
        listing.deleted_at = timezone.now()

    listing.save(update_fields=["is_deleted", "is_active"] + (["deleted_at"] if hasattr(listing, "deleted_at") else []))

    return JsonResponse({"ok": True})


@login_required
@require_POST
def republish_listing_api(request, listing_id):
    """
    Republish a listing (ad or request).
    - Free if ≥7 days since last republish
    - Costs 20 points if <7 days
    """
    listing = get_object_or_404(Listing, pk=listing_id, user=request.user)

    # ✅ Block if featured
    if listing.featured_until and listing.featured_until > timezone.now():
        return JsonResponse({
            "ok": False,
            "error": "cannot_republish_featured"
        }, status=400)

    # ✅ Block if not active/approved
    if not listing.is_approved or not listing.is_active:
        return JsonResponse({
            "ok": False,
            "error": "listing_not_active"
        }, status=400)

    now = timezone.now()
    last_publish = listing.published_at or listing.created_at
    days_since = (now.date() - last_publish.date()).days

    if days_since >= 7:
        cost = 0
    else:
        cost = 20

        # ✅ Use the new spend_points function
        try:
            spend_points(
                user=request.user,
                amount=cost,
                reason="republish_listing",
                meta={
                    "listing_id": listing.id,
                    "listing_title": listing.title,
                    "days_since_last": days_since,
                }
            )
        except NotEnoughPoints:
            return JsonResponse({
                "ok": False,
                "error": "not_enough_points"
            }, status=400)

        notify(
            user=request.user,
            kind=K_WALLET,
            status=S_USED,
            title="تم خصم نقاط",
            body=f"تم خصم {cost} نقطة مقابل إعادة نشر \"{listing.title}\" قبل انتهاء 7 أيام.",
            listing=listing,
        )

    # ✅ Update published_at to NOW
    listing.published_at = now
    listing.is_active = True
    listing.save(update_fields=["published_at", "is_active"])

    request.user.refresh_from_db(fields=["points"])

    return JsonResponse({
        "ok": True,
        "cost": cost,
        "free": (cost == 0),
        "points_balance": request.user.points,
        "published_at": listing.published_at.isoformat(),
    })


@login_required
@require_POST
def toggle_favorite(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    # Prevent favoriting your own item
    if item.listing.user == request.user:
        # AJAX case
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "is_favorited": False,
                "error": "cannot_favorite_own_item"
            }, status=400)

        # Normal POST case
        messages.info(request, "ℹ️ You cannot favorite your own item.")
        return redirect("item_detail", item_id=item.id)

    # Toggle favorite
    fav, created = Favorite.objects.get_or_create(
        user=request.user,
        listing=item.listing
    )

    if created:
        is_favorited = True
        messages.success(request, "⭐ Added to your favorites.")

        owner = item.listing.user
        if owner.user_id != request.user.user_id:

            notify(
                user=owner,
                kind=K_FAV,
                status=S_ADDED,
                title="تم إضافة إعلانك للمفضلة",
                body=f"قام أحد المستخدمين بإضافة إعلانك \"{item.listing.title}\" إلى المفضلة.",
                listing=item.listing,
            )


    else:
        fav.delete()
        is_favorited = False
        messages.info(request, "✳️ Removed from your favorites.")

    # AJAX request — return JSON only (NO PAGE REFRESH)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        new_count = Favorite.objects.filter(user=request.user).count()
        return JsonResponse({
            "is_favorited": is_favorited,
            "favorite_count": new_count
        })

    # Normal POST (from item detail page)
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(next_url)