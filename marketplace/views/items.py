import json
import uuid

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Exists, OuterRef
from django.contrib import messages
from django.views.decorators.http import require_GET

from elasticsearch import NotFoundError, Elasticsearch

from market_place import settings
from market_place.settings import IS_RENDER
from marketplace.documents import ListingDocument
from marketplace.forms import ItemForm, RequestForm
from marketplace.models import Listing, Favorite, Item, Category, Store, City, IssuesReport, ItemAttributeValue, \
    ItemPhoto
from marketplace.services.notifications import K_AD, S_PENDING, notify
from marketplace.utils.category_tree import get_selected_category_path, build_category_tree
from marketplace.views.helpers import _category_descendant_ids

from datetime import timedelta


def item_list(request):
    # ✅ keep your cleanup
    Listing.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=1000),
        type="item",
        is_active=True
    ).update(is_active=False)

    now = timezone.now()
    q = request.GET.get("q", "").strip()

    category_id_single = request.GET.get("category")
    category_ids_multi = request.GET.getlist("categories")
    city_id = request.GET.get("city")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    condition = (request.GET.get("condition") or "").strip()

    seller_type = (request.GET.get("seller_type") or "").strip()
    time_hours = (request.GET.get("time") or "").strip()
    sort = (request.GET.get("sort") or "").strip()

    fav_exists = None
    if request.user.is_authenticated:
        fav_exists = Exists(
            Favorite.objects.filter(
                user=request.user,
                listing=OuterRef("listing"),
            )
        )

    featured_items = (
        Item.objects.filter(
            listing__type="item",
            listing__is_approved=True,
            listing__is_active=True,
            listing__is_deleted=False,
            listing__featured_until__gt=now,
        )
        .select_related("listing", "listing__category", "listing__city", "listing__user")
        .prefetch_related("photos")
        .order_by("-listing__featured_until", "-listing__created_at")[:12]
    )

    if fav_exists is not None:
        featured_items = featured_items.annotate(is_favorited=fav_exists)

    base_qs = Item.objects.filter(
        listing__type="item",
        listing__is_approved=True,
        listing__is_active=True,
        listing__is_deleted=False
    ).order_by("-listing__featured_until")

    # ✅ ADD THIS: annotate base_qs (so every later queryset keeps it)
    if fav_exists is not None:
        base_qs = base_qs.annotate(is_favorited=fav_exists)

    selected_category = None

    if category_id_single:
        try:
            selected_category = Category.objects.get(id=category_id_single)
            ids = _category_descendant_ids(selected_category)
            base_qs = base_qs.filter(listing__category_id__in=ids)
        except Category.DoesNotExist:
            selected_category = None

    elif category_ids_multi:
        all_ids = []
        for cid in category_ids_multi:
            try:
                cat = Category.objects.get(id=cid)
                all_ids += _category_descendant_ids(cat)
            except Category.DoesNotExist:
                continue
        if all_ids:
            base_qs = base_qs.filter(listing__category_id__in=all_ids)

    if city_id:
        base_qs = base_qs.filter(listing__city_id=city_id)

    if min_price:
        base_qs = base_qs.filter(price__gte=min_price)
    if max_price:
        base_qs = base_qs.filter(price__lte=max_price)

    if condition:
        base_qs = base_qs.filter(condition=condition)

    if seller_type:
        if Store is not None:
            if seller_type == "store":
                base_qs = base_qs.filter(listing__user__store__isnull=False)
            elif seller_type == "individual":
                base_qs = base_qs.filter(listing__user__store__isnull=True)

    if time_hours:
        try:
            hours = int(time_hours)
            since = now - timedelta(hours=hours)
            base_qs = base_qs.filter(listing__created_at__gte=since)
        except ValueError:
            pass

    if sort == "priceAsc":
        queryset = base_qs.order_by("price", "-listing__created_at")
    elif sort == "priceDesc":
        queryset = base_qs.order_by("-price", "-listing__created_at")
    else:
        queryset = base_qs.order_by("-listing__created_at")

    if len(q) >= 2:
        if not IS_RENDER and hasattr(ListingDocument, "search"):
            try:
                from elasticsearch_dsl.query import Q as ES_Q

                es_query = ES_Q("multi_match", query=q, fields=["title", "description"], fuzziness="AUTO")
                hits = (
                    ListingDocument.search()
                    .query(es_query)
                    .filter("term", type="item")
                    [:50]
                    .execute()
                    .hits
                )
                listing_ids = [hit.meta.id for hit in hits]

                if listing_ids:
                    qs_list = list(
                        base_qs.filter(listing_id__in=listing_ids)
                        .select_related("listing__category", "listing__city", "listing__user")
                        .prefetch_related("photos")
                    )
                    qs_list.sort(key=lambda i: listing_ids.index(i.listing_id))
                    queryset = qs_list
                else:
                    queryset = base_qs.filter(listing__title__icontains=q)

            except Exception as e:
                print("[WARN] ES DOWN:", e)
                queryset = base_qs.filter(listing__title__icontains=q)
        else:
            queryset = base_qs.filter(
                Q(listing__title__icontains=q) | Q(listing__description__icontains=q)
            ).order_by("-listing__created_at")

    if isinstance(queryset, list):
        ids = [obj.id for obj in queryset]
        queryset = Item.objects.filter(id__in=ids).order_by("-listing__created_at")

        if fav_exists is not None:
            queryset = queryset.annotate(is_favorited=fav_exists)

    queryset = queryset.select_related(
        "listing",
        "listing__category",
        "listing__city",
        "listing__user"
    ).prefetch_related("photos")

    PAGE_SIZE = 27
    paginator = Paginator(queryset, PAGE_SIZE)
    page_number = request.GET.get("page") or "1"
    page_obj = paginator.get_page(page_number)

    total_count = paginator.count
    visible_count = page_obj.end_index() if total_count else 0
    has_more = page_obj.has_next()

    categories = Category.objects.filter(parent__isnull=True).prefetch_related("subcategories").distinct()
    cities = City.objects.all().order_by("name_ar")

    context = {
        "page_obj": page_obj,
        "items": page_obj.object_list,
        "q": q,
        "selected_category": selected_category,
        "categories": categories,
        "cities": cities,
        "selected_categories": request.GET.getlist("categories"),
        "total_count": total_count,
        "visible_count": visible_count,
        "featured_items": featured_items,
        "has_more": has_more,
        "filters": {
            "category": category_id_single or "",
            "city": city_id or "",
            "condition": condition,
            "seller_type": seller_type,
            "time": time_hours,
            "sort": sort or "latest",
            "min_price": min_price,
            "max_price": max_price,
        }
    }

    is_hx = bool(request.headers.get("HX-Request"))
    is_xhr = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_hx:
        html = render_to_string("partials/item_results.html", context, request=request)
        return HttpResponse(html)

    if is_xhr:
        html = render_to_string("partials/item_results.html", context, request=request)
        return JsonResponse({
            "html": html,
            "total_count": total_count,
            "visible_count": visible_count,
            "has_more": has_more,
        })

    return render(request, "item_list.html", context)


def item_detail(request, item_id):
    item = get_object_or_404(
        Item.objects.select_related("listing", "listing__user", "listing__category"),
        id=item_id,
        listing__is_approved=True,
        listing__is_active=True,
        listing__is_deleted=False,
    )

    listing = item.listing

    # ✅ Increment views (once per session per item)
    session_key = f"item_viewed_{item_id}"
    if not request.session.get(session_key):
        from django.db.models import F
        Listing.objects.filter(pk=listing.pk).update(views_count=F("views_count") + 1)
        request.session[session_key] = True
        listing.refresh_from_db(fields=["views_count"])

    breadcrumb_categories = []
    cat = getattr(item.listing, "category", None)
    while cat:
        breadcrumb_categories.append(cat)
        cat = cat.parent
    breadcrumb_categories.reverse()

    attributes = []
    for av in item.attribute_values.select_related("attribute").prefetch_related("attribute__options"):
        attr = av.attribute
        value = av.value

        if attr.input_type == "select" and value:
            option = None
            try:
                option_id = int(value)
                option = attr.options.filter(id=option_id).first()
            except (TypeError, ValueError):
                option = None

            if option:
                value = option.value_ar

        attributes.append({"name": attr.name_ar, "value": value})

    # ----------------------------
    # Similar items (fallback + ES)
    # ----------------------------
    def fallback_similar():
        return (
            Item.objects.filter(
                listing__category=item.listing.category,
                listing__is_approved=True,
                listing__is_active=True,
                listing__is_deleted=False
            )
            .exclude(id=item.id)
            .select_related("listing__category", "listing__city", "listing__user")
            .order_by("-listing__published_at")[:4]
        )

    similar_items = fallback_similar()

    if not getattr(settings, "IS_RENDER", False):
        try:
            es = Elasticsearch(settings.ELASTICSEARCH_DSL["default"]["hosts"])

            query = {
                "query": {
                    "more_like_this": {
                        "fields": ["title", "description"],
                        "like": [{"_index": "items", "_id": item.id}],
                        "min_term_freq": 1,
                        "max_query_terms": 12,
                    }
                },
                "size": 4,
            }

            response = es.search(index="items", body=query)
            hits = response.get("hits", {}).get("hits", [])
            ids = [hit["_id"] for hit in hits]

            if ids:
                es_items = (
                    Item.objects.filter(
                        id__in=ids,
                        listing__is_approved=True,
                        listing__is_active=True,
                        listing__is_deleted=False
                    )
                    .exclude(id=item.id)
                    .select_related("listing__category", "listing__city", "listing__user")
                    .order_by("-listing__published_at")[:4]
                )

                if es_items.exists():
                    similar_items = es_items

        except (ConnectionError, NotFoundError, Exception) as e:
            print("[WARN] Elasticsearch error in item_detail:", e)


    fav_listing_ids = set()
    if request.user.is_authenticated:
        fav_listing_ids = set(
            Favorite.objects.filter(user=request.user).values_list("listing_id", flat=True)
        )

    # main item (used by the big fav button)
    is_favorited = bool(item.listing_id in fav_listing_ids) if request.user.is_authenticated else False

    # similar cards (partials/_item_card.html expects item.is_favorited)
    similar_items = list(similar_items)
    for it in similar_items:
        it.is_favorited = bool(it.listing_id in fav_listing_ids) if request.user.is_authenticated else False

    seller = item.listing.user
    raw_phone = (seller.phone or "").strip()

    seller_phone_masked = "07•• ••• •••"
    if raw_phone:
        first2 = raw_phone[:2] if len(raw_phone) >= 2 else raw_phone
        seller_phone_masked = f"{first2}•• ••• •••"

    can_send_full_phone = bool(item.listing.show_phone) and request.user.is_authenticated
    seller_phone_full = raw_phone if can_send_full_phone else ""

    seller_is_store = hasattr(seller, "store") and seller.store is not None
    store = seller.store if seller_is_store else None
    seller_is_verified_store = bool(store and getattr(store, "is_verified", False))

    reviews = []
    if seller_is_store:
        reviews = store.reviews.select_related("reviewer").order_by("-created_at")[:10]
    seller_reviews_count = len(reviews)

    seller_items_count = Listing.objects.filter(
        user=seller,
        type="item",
        is_active=True,
        is_approved=True,
    ).count()

    reported_already = False
    if request.user.is_authenticated:
        reported_already = IssuesReport.objects.filter(
            user=request.user,
            target_kind="listing",
            listing=item.listing,
            listing_type="item",
        ).exists()

    is_own_listing = False
    if request.user.is_authenticated:
        is_own_listing = (item.listing.user_id == request.user.user_id)

    return render(request, "item_detail.html", {
        "item": item,
        "attributes": attributes,
        "similar_items": similar_items,

        "is_favorited": is_favorited,

        "seller_items_count": seller_items_count,
        "seller_reviews_count": seller_reviews_count,
        "seller_is_store": seller_is_store,
        "seller_is_verified_store": seller_is_verified_store,
        "store_reviews": reviews,
        "store": store,

        "allow_show_phone": item.listing.show_phone,
        "seller_phone_masked": seller_phone_masked,
        "seller_phone_full": seller_phone_full,

        "report_kind": "item",
        "reported_already": reported_already,
        "breadcrumb_categories": breadcrumb_categories,
        "is_own_listing": is_own_listing,
    })


@login_required
@transaction.atomic
def item_create(request):
    # =============================
    # 1. Top-level categories
    # =============================
    lang = translation.get_language()
    order_field = "name_ar" if lang == "ar" else "name_en"

    top_categories = Category.objects.filter(parent__isnull=True).order_by(order_field)

    category_id = request.POST.get("category") or request.GET.get("category")
    selected_category = Category.objects.filter(id=category_id).first() if category_id else None

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, category=selected_category)

        print("=== DEBUG: item_create POST ===")
        print("selected_category_id:", category_id, " resolved:", selected_category)
        print("POST keys:", list(request.POST.keys()))
        print("FILES keys:", list(request.FILES.keys()))
        print("FILES images count:", len(request.FILES.getlist('images')))
        print("Form fields:", list(form.fields.keys()))
        print("================================")

        if form.is_valid() and selected_category:
            print("=== DEBUG: form is valid ===")

            # -----------------------------
            # 2. Create LISTING
            # -----------------------------
            listing = form.save(commit=False)
            listing.category = selected_category
            listing.user = request.user
            listing.type = "item"                      # IMPORTANT
            listing.is_approved = False
            listing.is_active = True
            listing.show_phone = (request.POST.get("show_phone") == "on")
            listing.save()

            item = Item.objects.create(
                listing=listing,
                price=form.cleaned_data["price"],
                condition=form.cleaned_data["condition"],
            )

            images = request.FILES.getlist("images")
            main_index = request.POST.get("main_photo_index")
            main_index = int(main_index) if main_index and main_index.isdigit() else None

            for idx, img in enumerate(images):
                photo = ItemPhoto.objects.create(item=item, image=img)
                if main_index is not None and idx == main_index:
                    photo.is_main = True
                    photo.save()

            if images and not item.photos.filter(is_main=True).exists():
                first = item.photos.first()
                if first:
                    first.is_main = True
                    first.save()


            for field_name, value in form.cleaned_data.items():
                if not field_name.startswith("attr_"):
                    continue
                if field_name.endswith("_other"):
                    continue

                try:
                    attr_id = int(field_name.split("_")[1])
                except Exception:
                    continue

                attribute = selected_category.attributes.filter(id=attr_id).first()
                if not attribute:
                    continue

                if isinstance(value, list):
                    parts = []
                    for v in value:
                        if v == "__other__":
                            other_text = (form.cleaned_data.get(f"{field_name}_other") or "").strip()
                            if other_text:
                                parts.append(other_text)
                        else:
                            parts.append(str(v))
                    final_value = ", ".join(parts) if parts else ""
                else:
                    if value == "__other__":
                        final_value = (form.cleaned_data.get(f"{field_name}_other") or "").strip()
                    else:
                        final_value = str(value).strip() if value is not None else ""

                if final_value:
                    ItemAttributeValue.objects.create(
                        item=item,
                        attribute_id=attr_id,
                        value=final_value,
                    )

            notify(
                user=request.user,
                kind=K_AD,
                status=S_PENDING,
                title="إعلانك قيد المراجعة",
                body=f"إعلانك \"{listing.title}\" قيد المراجعة حالياً.",
                listing=listing,
            )

            messages.success(request, "✅ Your ad was submitted (pending review).")
            return redirect("my_account")

        request.session["item_create_form_token"] = str(uuid.uuid4())

        return render(
            request,
            "item_create.html",
            {
                "form": form,
                "top_categories": top_categories,
                "categories": top_categories,
                "selected_category": selected_category,
                "debug_info": {
                    "post_keys": list(request.POST.keys()),
                    "files_keys": list(request.FILES.keys()),
                    "images_count": len(request.FILES.getlist("images")),
                    "form_fields": list(form.fields.keys()),
                    "errors_html": form.errors.as_ul(),
                    "non_field_errors_html": form.non_field_errors(),
                    "form_token": request.session["item_create_form_token"],
                },
            },
        )

    form = ItemForm(category=selected_category)

    category_tree = build_category_tree(top_categories, lang)
    category_tree_json = json.dumps(category_tree, ensure_ascii=False)

    selected_path = get_selected_category_path(selected_category)
    selected_path_json = json.dumps(selected_path)

    request.session["item_create_form_token"] = str(uuid.uuid4())


    return render(
        request,
        "item_create.html",
        {
            "form": form,
            "top_categories": top_categories,
            "categories": top_categories,
            "selected_category": selected_category,
            "category_tree_json": category_tree_json,
            "selected_category_path_json": selected_path_json,
            "form_token": request.session["item_create_form_token"],
        },
    )


@login_required
@transaction.atomic
def item_edit(request, item_id):
    now = timezone.now()
    item = get_object_or_404(
        Item.objects.select_related("listing", "listing__category", "listing__user").filter(
            listing__user=request.user,
            listing__is_deleted=False,
        ).filter(
            Q(listing__featured_until__isnull=True) | Q(listing__featured_until__lte=now)
        ),
        id=item_id,
    )

    listing = item.listing
    category = listing.category

    initial = {
        "price": item.price,
        "condition": item.condition,
    }

    form = ItemForm(
        request.POST or None,
        request.FILES or None,
        category=category,
        initial=initial,
        instance=listing,
    )

    if request.method == "POST" and form.is_valid():
        form.cleaned_data["category"] = item.listing.category
        listing = form.save(commit=False)
        listing.category = item.listing.category
        listing.is_approved = False
        listing.was_edited = True
        listing.save()

        item.price = form.cleaned_data.get("price")
        item.condition = form.cleaned_data.get("condition")
        item.save()

        for key in request.POST:
            if key.startswith("delete_photo_"):
                try:
                    photo_id = int(key.split("_")[-1])
                except ValueError:
                    continue
                ItemPhoto.objects.filter(id=photo_id, item=item).delete()

        ItemAttributeValue.objects.filter(item=item).delete()

        for field_name, value in form.cleaned_data.items():
            if not field_name.startswith("attr_"):
                continue
            if field_name.endswith("_other"):
                continue

            try:
                attr_id = int(field_name.split("_")[1])
            except Exception:
                continue

            if value is None or value == "":
                continue

            if isinstance(value, list):
                parts = []
                for v in value:
                    if v == "__other__":
                        other_text = form.cleaned_data.get(f"{field_name}_other", "").strip()
                        if other_text:
                            parts.append(other_text)
                    else:
                        parts.append(str(v))
                final_value = ", ".join(parts) if parts else ""
            else:
                if value == "__other__":
                    final_value = form.cleaned_data.get(f"{field_name}_other", "").strip()
                else:
                    final_value = str(value)

            if final_value:
                ItemAttributeValue.objects.create(
                    item=item,
                    attribute_id=attr_id,
                    value=final_value,
                )

        new_images = request.FILES.getlist("images")
        created_photos = [
            ItemPhoto.objects.create(item=item, image=img)
            for img in new_images
        ]

        selected_main_id = request.POST.get("selected_main_photo")
        main_index = request.POST.get("main_photo_index")
        main_index = int(main_index) if main_index and main_index.isdigit() else None

        ItemPhoto.objects.filter(item=item).update(is_main=False)

        if selected_main_id:
            ItemPhoto.objects.filter(id=selected_main_id, item=item).update(is_main=True)

        elif main_index is not None and 0 <= main_index < len(created_photos):
            created_photos[main_index].is_main = True
            created_photos[main_index].save()

        elif not item.photos.filter(is_main=True).exists():
            first = item.photos.first()
            if first:
                first.is_main = True
                first.save()

        notify(
            user=request.user,
            kind=K_AD,
            status=S_PENDING,
            title="تم إرسال إعلانك للمراجعة مجدداً",
            body=f"بعد التعديل، إعلانك \"{listing.title}\" بانتظار المراجعة.",
            listing=listing,
        )

        return redirect("my_account")

    return render(
        request,
        "item_edit.html",
        {
            "form": form,
            "item": item,
            "category": category,
        },
    )


@login_required
def item_attributes_partial(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    kind = (request.GET.get("kind") or "").strip().lower()
    listing_id = (request.GET.get("listing_id") or "").strip()

    item_instance = None
    request_instance = None

    if listing_id:
        listing = get_object_or_404(Listing, id=listing_id, user=request.user)

        kind = kind or listing.type
        if kind == "request":
            request_instance = getattr(listing, "request", None)
        else:
            item_instance = getattr(listing, "item", None)

    if kind == "request":
        form = RequestForm(category=category, instance=request_instance)
    else:
        form = ItemForm(category=category, instance=item_instance)

    return render(request, "partials/item_attributes.html", {"form": form})


@require_GET
def item_detail_more_similar(request, item_id):
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 12))

    item = get_object_or_404(Item, id=item_id)
    cat = getattr(item.listing, "category", None)

    qs = (
        Item.objects
        .filter(
            listing__type="item",
            listing__is_active=True,
            listing__is_approved=True,
            listing__is_deleted=False
        )
        .exclude(id=item.id)
        .select_related("listing__category", "listing__city", "listing__user")
        .prefetch_related("photos")
        .order_by("-listing__created_at")
    )

    if cat:
        qs = qs.filter(listing__category=cat)

    if request.user.is_authenticated:
        qs = qs.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(user=request.user, listing=OuterRef("listing"))
            )
        )

    chunk = list(qs[offset:offset + limit])

    html = render_to_string(
        "partials/_item_cards_only.html",
        {"items": chunk},
        request=request
    )

    has_more = qs.count() > (offset + limit)
    return JsonResponse({"html": html, "has_more": has_more})


def my_items(request):
    items = (
        Item.objects
        .filter(user=request.user)
        .order_by('-created_at')
        .select_related('category')
        .prefetch_related('photos')
    )

    paginator = Paginator(items, 8)   # 8 per page (you can change)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'my_items.html', {
        'page_obj': page_obj
    })

@login_required
def reactivate_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, listing__user=request.user)
    if not item.is_active:
        item.is_active = True
        item.save()
        messages.success(request, "✅ Your item is active again.")
    else:
        messages.info(request, "ℹ️ Item is already active.")
    return redirect('my_items')




@login_required
def delete_item_photo(request, photo_id):
    photo = get_object_or_404(ItemPhoto, id=photo_id)

    if photo.item.user != request.user:
        return HttpResponseForbidden("Not allowed")

    item_id = photo.item.id
    photo.image.delete(save=False)
    photo.delete()
    return redirect("item_edit", item_id=item_id)

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, listing__user=request.user)

    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    item.delete()

    # ✅ If called via fetch/AJAX -> return JSON redirect
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "redirect_url": "/my-account/#tab-ads"})

    # ✅ Normal browser POST fallback
    messages.success(request, "تم حذف الإعلان")

    resp = redirect("my_account")
    resp["Location"] += "#tab-ads"
    return resp


@login_required
def cancel_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, listing__user=request.user)

    if request.method == "POST":
        sold = request.POST.get("sold_on_site")
        reason = request.POST.get("reason", "").strip()

        # Only deactivate, don't change approval status
        item.is_active = False
        item.cancel_reason = reason
        item.sold_on_site = (sold == "yes")
        item.save(update_fields=["is_active", "cancel_reason", "sold_on_site"])

        messages.success(request, "✅ Your ad has been canceled (still approved for future reactivation).")
        return redirect("my_items")

    return render(request, "cancel_item.html", {"item": item})