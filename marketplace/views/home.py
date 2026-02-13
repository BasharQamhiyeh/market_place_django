from marketplace.models import Item, Favorite, Request, Category, Store
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.db.models import Count, Avg
from django.db.models import Exists, OuterRef


def home(request):
    limit = int(request.GET.get("limit", 12))
    latest_items = (
        Item.objects
        .filter(
            listing__type="item",
            listing__is_active=True,
            listing__is_approved=True,
            listing__is_deleted=False
        )
        .select_related("listing__category", "listing__city", "listing__user")
        .prefetch_related("photos")
        .order_by("-listing__published_at")[:limit]
    )

    if request.user.is_authenticated:
        latest_items = latest_items.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user=request.user,
                    listing=OuterRef("listing")
                )
            )
        )

    latest_requests = (
        Request.objects
        .filter(
            listing__type="request",
            listing__is_active=True,
            listing__is_approved=True,
            listing__is_deleted=False
        )
        .select_related("listing__category", "listing__city", "listing__user")
        .order_by("-listing__published_at")[:limit]
    )

    categories = (
        Category.objects
        .filter(parent__isnull=True)
        .prefetch_related("subcategories")
        .order_by("name_ar")
    )

    stores = (
        Store.objects
        .filter(is_active=True)  # if you have this field, otherwise remove
        .annotate(
            avg_rating=Avg("reviews__rating"),
            reviews_count=Count("reviews"),
        )
        .order_by("-avg_rating", "-reviews_count")[:12]
    )

    context = {
        "categories": categories,
        "latest_items": latest_items,
        "latest_requests": latest_requests,
        "stores": stores,
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/latest_items_block.html", context)

    return render(request, "home.html", context)



@require_GET
def home_more_items(request):
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 12))

    qs = (
        Item.objects
        .filter(
            listing__type="item",
            listing__is_active=True,
            listing__is_approved=True,
            listing__is_deleted=False
        )
        .select_related("listing__category", "listing__city", "listing__user")
        .prefetch_related("photos")
        .order_by("-listing__created_at")
    )

    if request.user.is_authenticated:
        qs = qs.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(user=request.user, listing=OuterRef("listing"))
            )
        )

    chunk = list(qs[offset:offset + limit])
    html = render_to_string("partials/_item_cards_only.html", {"items": chunk}, request=request)
    has_more = qs.count() > (offset + limit)

    return JsonResponse({"html": html, "has_more": has_more})


@require_GET
def home_more_requests(request):
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 12))

    qs = (
        Request.objects
        .filter(
            listing__type="request",
            listing__is_active=True,
            listing__is_approved=True,
            listing__is_deleted=False
        )
        .select_related("listing__category", "listing__city", "listing__user")
        .order_by("-listing__created_at")
    )

    chunk = list(qs[offset:offset + limit])
    html = render_to_string("partials/_request_cards_only.html", {"latest_requests": chunk}, request=request)
    has_more = qs.count() > (offset + limit)

    return JsonResponse({"html": html, "has_more": has_more})