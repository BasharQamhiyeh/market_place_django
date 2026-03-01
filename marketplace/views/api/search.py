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
                name__icontains=query
            ).select_related("parent")[:8]

            for c in categories:
                if c.id not in seen_categories:     # <<< FIX
                    seen_categories.add(c.id)
                    results.append({
                        "type": "category",
                        "name": c.name,
                        "parent": c.parent.name if c.parent else "",
                        "category_id": c.id,
                    })

            # ES → items
            for hit in es_results:
                try:
                    item = Item.objects.select_related("listing__category").prefetch_related("photos").get(id=hit.meta.id)
                except Item.DoesNotExist:
                    continue

                photo = item.main_photo
                results.append({
                    "type": "item",
                    "id": item.id,
                    "name": item.listing.title,
                    "category": item.listing.category.name if item.listing.category else "",
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
                .annotate(similarity=TrigramSimilarity("name", query))
                .filter(similarity__gt=0.2)
                .order_by("-similarity")[:8]
            )

            for c in categories:
                if c.id not in seen_categories:    # <<< FIX
                    seen_categories.add(c.id)
                    results.append({
                        "type": "category",
                        "name": c.name,
                        "parent": c.parent.name if c.parent else "",
                        "category_id": c.id,
                    })

            # items
            items = (
                Item.objects
                .filter(listing__is_approved=True, listing__is_active=True, listing__is_deleted=False)
                .annotate(similarity=TrigramSimilarity("listing__title", query))
                .filter(similarity__gt=0.2)
                .select_related("listing__category")
                .prefetch_related("photos")
                .order_by("-similarity")[:6]
            )

            for i in items:
                photo = i.main_photo
                results.append({
                    "type": "item",
                    "id": i.id,
                    "name": i.listing.title,
                    "category": i.listing.category.name if i.listing.category else "",
                    "photo_url": photo.image.url if photo else "",
                })

            return JsonResponse({"results": results})

        except Exception:
            pass

    # ============================================================
    # 3️⃣ FINAL FALLBACK: simple icontains
    # ============================================================
    categories = Category.objects.filter(
        name__icontains=query
    )[:8]

    for c in categories:
        if c.id not in seen_categories:    # <<< FIX
            seen_categories.add(c.id)
            results.append({
                "type": "category",
                "name": c.name,
                "parent": c.parent.name if c.parent else "",
                "category_id": c.id,
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
            "category": i.listing.category.name,
            "city": i.listing.city.name if i.listing.city else "",
            "price": i.price,
            "photo_url": i.main_photo.image.url if i.main_photo else "",
        })

    return JsonResponse({"results": results})