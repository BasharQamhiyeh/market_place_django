from django.shortcuts import get_object_or_404, render

from marketplace.models import User, Listing, Category, City, IssuesReport


def user_profile(request, user_id):
    seller = get_object_or_404(User, pk=user_id, is_active=True)

    # ✅ Increment profile views once per session per user
    session_key = f"user_viewed_{user_id}"
    if not request.session.get(session_key):
        # User.objects.filter(pk=seller.pk).update(views_count=F("views_count") + 1)
        request.session[session_key] = True
        # seller.refresh_from_db(fields=["views_count"])

    # ✅ IMPORTANT:
    # The template includes the card with `item=l.item`
    # So we MUST return Listing objects, but only those that actually have a related Item.
    listings_qs = (
        Listing.objects
        .filter(
            user=seller,
            is_active=True,
            is_approved=True,
            type="item",
            item__isnull=False,          # ✅ excludes broken listings (no Item)
        )
        .select_related("category", "city", "user")
        .prefetch_related("item")       # ✅ avoid extra queries when template accesses l.item
        .order_by("-published_at")
    )

    listings = list(listings_qs[:30])

    listings_count = listings_qs.count()

    def _root_category(cat):
        while cat and cat.parent_id:
            cat = cat.parent
        return cat

    for l in listings:
        # ✅ No need to touch l.item.listing/category; Listing already has category/city
        root = _root_category(getattr(l, "category", None))
        l.root_category_id = root.id if root else ""

        l._city_id = getattr(l, "city_id", None) or ""

    categories = Category.objects.filter(parent__isnull=True).order_by("name_ar")
    cities = City.objects.filter(is_active=True).order_by("name_ar")

    full_phone = seller.phone if getattr(seller, "phone", None) else ""
    masked_phone = "07•• ••• •••"

    # ✅ reporting state
    reported_already = False
    is_own_profile = False
    if request.user.is_authenticated:
        is_own_profile = (seller.user_id == request.user.user_id)
        reported_already = IssuesReport.objects.filter(
            user=request.user,
            target_kind="user",
            reported_user=seller,
        ).exists()

    avatar_url = seller.profile_photo.url if getattr(seller, "profile_photo", None) else None

    ctx = {
        "seller": seller,
        "listings": listings,                 # ✅ still listings (so l.item works in template)
        "listings_count": listings_count,
        "categories": categories,
        "cities": cities,
        "full_phone": full_phone,
        "masked_phone": masked_phone,
        "reported_already": reported_already,
        "is_own_profile": is_own_profile,
        "avatar_url": avatar_url,
    }
    return render(request, "user_profile.html", ctx)