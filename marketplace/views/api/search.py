from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from marketplace.documents import ListingDocument
from marketplace.models import Category, Item
from marketplace.models.requests import Request
from marketplace.views.constants import IS_RENDER, TRIGRAM_AVAILABLE


@require_GET
def search_suggestions(request):
    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("type", "item")  # "item" or "request"

    if len(query) < 2:
        return JsonResponse({"results": []})

    listing_results = []   # items or requests go here
    category_results = []  # categories go here
    seen_categories = set()

    # ============================================================
    # 1️⃣ TRY ELASTICSEARCH FIRST
    # ============================================================
    if not IS_RENDER and hasattr(ListingDocument, "search"):
        try:
            from elasticsearch_dsl.query import Q as ES_Q

            es_query = ES_Q(
                "multi_match",
                query=query,
                fields=[
                    "title^3",
                    "title.edge_ngram",
                    "category.name",
                    "attributes.name",
                    "city.name",
                    "description",
                ],
                fuzziness="AUTO",
            )

            es_results = ListingDocument.search().query(es_query)[:6].execute()
            listing_ids = [int(hit.meta.id) for hit in es_results]

            # categories via DB
            for c in Category.objects.filter(name__icontains=query).select_related("parent", "photo")[:8]:
                if c.id not in seen_categories:
                    seen_categories.add(c.id)
                    category_results.append({
                        "type": "category",
                        "name": c.name,
                        "parent": c.parent.name if c.parent else "",
                        "category_id": c.id,
                        "photo_url": c.photo_url or "",
                    })

            # ES hit.meta.id is a Listing ID
            if search_type == "request":
                approved_ids = set(
                    Request.objects
                    .filter(
                        listing_id__in=listing_ids,
                        listing__is_approved=True,
                        listing__is_active=True,
                        listing__is_deleted=False,
                    )
                    .values_list("listing_id", flat=True)
                )
                for hit in es_results:
                    hit_id = int(hit.meta.id)
                    if hit_id not in approved_ids:
                        continue
                    try:
                        req = Request.objects.select_related("listing__category").get(listing_id=hit_id)
                    except Request.DoesNotExist:
                        continue
                    listing_results.append({
                        "type": "request",
                        "id": req.id,
                        "name": req.listing.title,
                        "category": req.listing.category.name if req.listing.category else "",
                        "budget": str(req.budget) if req.budget else "",
                    })
            else:
                approved_ids = set(
                    Item.objects
                    .filter(
                        listing_id__in=listing_ids,
                        listing__is_approved=True,
                        listing__is_active=True,
                        listing__is_deleted=False,
                    )
                    .values_list("listing_id", flat=True)
                )
                for hit in es_results:
                    hit_id = int(hit.meta.id)
                    if hit_id not in approved_ids:
                        continue
                    try:
                        item = Item.objects.select_related("listing__category").prefetch_related("photos").get(listing_id=hit_id)
                    except Item.DoesNotExist:
                        continue
                    photo = item.main_photo
                    listing_results.append({
                        "type": "item",
                        "id": item.id,
                        "name": item.listing.title,
                        "category": item.listing.category.name if item.listing.category else "",
                        "photo_url": photo.image.url if photo else "",
                    })

            return JsonResponse({"results": listing_results + category_results})

        except Exception:
            pass  # ES down → fallback

    # ============================================================
    # 2️⃣ FALLBACK: trigram word-similarity (with icontains fallback)
    # ============================================================
    # TrigramWordSimilarity compares the query against each individual
    # word in the title — far better for Arabic than whole-string similarity.
    # Threshold 0.4 catches plural↔singular variants ("سيارات"↔"سيارة" → 0.57)
    # without producing false positives for unrelated words.
    WORD_SIM_THRESHOLD = 0.4

    for c in Category.objects.filter(name__icontains=query).select_related("parent", "photo")[:8]:
        if c.id not in seen_categories:
            seen_categories.add(c.id)
            category_results.append({
                "type": "category",
                "name": c.name,
                "parent": c.parent.name if c.parent else "",
                "category_id": c.id,
                "photo_url": c.photo_url or "",
            })

    approved_base = {
        "listing__is_approved": True,
        "listing__is_active": True,
        "listing__is_deleted": False,
    }
    # Match: title contains query  OR  title is word-similar  OR  category name contains query
    text_match = (
        Q(listing__title__icontains=query)
        | Q(listing__category__name__icontains=query)
    )

    if search_type == "request":
        rows = None
        if TRIGRAM_AVAILABLE:
            try:
                from django.contrib.postgres.search import TrigramWordSimilarity
                rows = list(
                    Request.objects
                    .filter(**approved_base)
                    .select_related("listing__category")
                    .annotate(word_sim=TrigramWordSimilarity(query, "listing__title"))
                    .filter(text_match | Q(word_sim__gte=WORD_SIM_THRESHOLD))
                    .order_by("-word_sim")[:6]
                )
            except Exception:
                pass
        if rows is None:
            rows = list(
                Request.objects
                .filter(text_match, **approved_base)
                .select_related("listing__category")[:6]
            )
        for r in rows:
            listing_results.append({
                "type": "request",
                "id": r.id,
                "name": r.listing.title,
                "category": r.listing.category.name if r.listing.category else "",
                "budget": str(r.budget) if r.budget else "",
            })
    else:
        rows = None
        if TRIGRAM_AVAILABLE:
            try:
                from django.contrib.postgres.search import TrigramWordSimilarity
                rows = list(
                    Item.objects
                    .filter(**approved_base)
                    .select_related("listing__category")
                    .prefetch_related("photos")
                    .annotate(word_sim=TrigramWordSimilarity(query, "listing__title"))
                    .filter(text_match | Q(word_sim__gte=WORD_SIM_THRESHOLD))
                    .order_by("-word_sim")[:6]
                )
            except Exception:
                pass
        if rows is None:
            rows = list(
                Item.objects
                .filter(text_match, **approved_base)
                .select_related("listing__category")
                .prefetch_related("photos")[:6]
            )
        for i in rows:
            photo = i.main_photo
            listing_results.append({
                "type": "item",
                "id": i.id,
                "name": i.listing.title,
                "category": i.listing.category.name if i.listing.category else "",
                "photo_url": photo.image.url if photo else "",
            })

    return JsonResponse({"results": listing_results + category_results})
