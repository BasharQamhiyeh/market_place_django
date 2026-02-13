from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from marketplace.documents import ListingDocument
from marketplace.models import Category, Item
from marketplace.views.constants import IS_RENDER, TRIGRAM_AVAILABLE


@require_GET
def search_suggestions(request):
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})

    results = []
    seen_categories = set()   # <<< FIX ADDED

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
                    "title.ngram",
                    "category.name",
                    "attributes.name",
                    "city.name",
                    "description",
                ],
                fuzziness="AUTO",
            )

            es_results = ListingDocument.search().query(es_query)[:6].execute()

            # categories via DB
            categories = Category.objects.filter(
                Q(name_ar__icontains=query) | Q(name_en__icontains=query)
            ).select_related("parent")[:8]

            for c in categories:
                if c.id not in seen_categories:     # <<< FIX
                    seen_categories.add(c.id)
                    results.append({
                        "type": "category",
                        "name": c.name_ar,
                        "parent": c.parent.name_ar if c.parent else "",
                        "category_id": c.id,
                        "emoji": c.icon or "📂",
                    })

            # ES → items
            for hit in es_results:
                try:
                    item = Item.objects.select_related("category").prefetch_related("photos").get(id=hit.meta.id)
                except Item.DoesNotExist:
                    continue

                photo = item.photos.first()
                results.append({
                    "type": "item",
                    "id": item.id,
                    "name": item.title,
                    "category": item.category.name_ar if item.category else "",
                    "photo_url": photo.image.url if photo else "",
                })

            return JsonResponse({"results": results})

        except Exception:
            pass  # ES DOWN → fallback

    # ============================================================
    # 2️⃣ FALLBACK: POSTGRES TRIGRAM IF AVAILABLE
    # ============================================================
    if TRIGRAM_AVAILABLE:
        try:
            # categories
            categories = (
                Category.objects
                .annotate(similarity=TrigramSimilarity("name_ar", query))
                .filter(similarity__gt=0.2)
                .order_by("-similarity")[:8]
            )

            for c in categories:
                if c.id not in seen_categories:    # <<< FIX
                    seen_categories.add(c.id)
                    results.append({
                        "type": "category",
                        "name": c.name_ar,
                        "parent": c.parent.name_ar if c.parent else "",
                        "category_id": c.id,
                        "emoji": c.icon or "📂",
                    })

            # items
            items = (
                Item.objects.filter(is_approved=True, is_active=True)
                .annotate(similarity=TrigramSimilarity("title", query))
                .filter(similarity__gt=0.2)
                .select_related("category")
                .prefetch_related("photos")
                .order_by("-similarity")[:6]
            )

            for i in items:
                photo = i.photos.first()
                results.append({
                    "type": "item",
                    "id": i.id,
                    "name": i.title,
                    "category": i.category.name_ar if i.category else "",
                    "photo_url": photo.image.url if photo else "",
                })

            return JsonResponse({"results": results})

        except Exception:
            pass

    # ============================================================
    # 3️⃣ FINAL FALLBACK: simple icontains
    # ============================================================
    categories = Category.objects.filter(
        Q(name_ar__icontains=query) | Q(name_en__icontains=query)
    )[:8]

    for c in categories:
        if c.id not in seen_categories:    # <<< FIX
            seen_categories.add(c.id)
            results.append({
                "type": "category",
                "name": c.name_ar,
                "parent": c.parent.name_ar if c.parent else "",
                "category_id": c.id,
                "emoji": c.icon or "📂",
            })

    # ---- ITEMS MATCHING TITLE ----
    items = Item.objects.filter(
        Q(listing__title__icontains=query),
        listing__is_approved=True,
        listing__is_active=True,
        listing__is_deleted=False
    ).select_related("listing", "listing__category").prefetch_related("photos")[:6]

    for i in items:
        results.append({
            "type": "item",
            "id": i.id,
            "name": i.listing.title,
            "category": i.listing.category.name_ar,
            "city": i.listing.city.name_ar if i.listing.city else "",
            "price": i.price,
            "emoji": i.listing.category.icon or "🛒",
            "photo_url": i.main_photo.image.url if i.main_photo else "",
        })

    return JsonResponse({"results": results})