# Django auth
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password

# Django admin
from django.contrib.admin.views.decorators import staff_member_required

# Django HTTP / views
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST


# Django core
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Avg
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.contrib.postgres.search import TrigramSimilarity
from django.urls import reverse

from .models import (
    City,
    Category,
    ItemPhoto,
    ItemAttributeValue,
    Notification,
    Subscriber,
    Conversation,
    Message,
    Item,
    Attribute,
    AttributeOption,
    IssuesReport,
    Favorite,
    User,
    Request,
    Listing,
    RequestAttributeValue, Store, StoreReview, StoreFollow
)

from .forms import (
    ItemForm,
    UserProfileEditForm,
    UserPasswordChangeForm,
    PhoneVerificationForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    RequestForm, SignupAfterOtpForm, UserRegistrationForm, StoreReviewForm
)
from .utils.service import recalc_store_rating

# Local imports
from .validators import validate_no_links_or_html
from .documents import ListingDocument
from .utils.category_tree import build_category_tree, get_selected_category_path
from .utils.sms import send_sms_code
from .utils.verification import send_code, verify_session_code

# Elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, TransportError
from elasticsearch_dsl.query import Q as ES_Q

# Standard library
from collections import deque
from datetime import timedelta
import json
import re



from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login

from .models import User
import uuid
from django.http import HttpResponseBadRequest

from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.db.models import Q, Exists, OuterRef
from .models import User

try:
    from django.contrib.postgres.search import TrigramSimilarity
    TRIGRAM_AVAILABLE = True
except Exception:
    TRIGRAM_AVAILABLE = False


IS_RENDER = getattr(settings, "IS_RENDER", False)


# NEW HOMEPAGE VIEW (replaces item_list as homepage)
def home(request):
    limit = int(request.GET.get("limit", 12))

    latest_items = (
        Item.objects
        .filter(
            listing__type="item",
            listing__is_active=True,
            listing__is_approved=True,
        )
        .select_related("listing__category", "listing__city", "listing__user")
        .prefetch_related("photos")
        .order_by("-listing__created_at")[:limit]
    )

    from django.db.models import Exists, OuterRef

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
        )
        .select_related("listing__category", "listing__city", "listing__user")
        .order_by("-listing__created_at")[:limit]
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

    # HTMX partial for "أحدث الإعلانات"
    if request.headers.get("HX-Request"):
        return render(request, "partials/latest_items_block.html", context)

    return render(request, "home.html", context)




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

    # ✅ FAVORITE exists subquery (same as home)
    fav_exists = None
    if request.user.is_authenticated:
        fav_exists = Exists(
            Favorite.objects.filter(
                user=request.user,
                listing=OuterRef("listing"),
            )
        )

    # ✅ Featured from DB (independent of filters/search)
    featured_items = (
        Item.objects.filter(
            listing__type="item",
            listing__is_approved=True,
            listing__is_active=True,
            listing__featured_until__gt=now,
        )
        .select_related("listing", "listing__category", "listing__city", "listing__user")
        .prefetch_related("photos")
        .order_by("-listing__featured_until", "-listing__created_at")[:12]
    )

    if fav_exists is not None:
        featured_items = featured_items.annotate(is_favorited=fav_exists)

    # ✅ Normal results (exclude featured so they don't repeat)
    base_qs = Item.objects.filter(
        listing__type="item",
        listing__is_approved=True,
        listing__is_active=True,
    )

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

    # ✅ Search logic
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

    # if search returned list, rehydrate queryset
    if isinstance(queryset, list):
        ids = [obj.id for obj in queryset]
        queryset = Item.objects.filter(id__in=ids).order_by("-listing__created_at")

        # ✅ CRITICAL: re-annotate after rebuilding queryset
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


def request_list(request):
    now = timezone.now()

    q = (request.GET.get("q") or "").strip()

    category_id_single = request.GET.get("category")
    category_ids_multi = request.GET.getlist("categories")
    city_id = request.GET.get("city")

    min_budget = request.GET.get("min_budget")
    max_budget = request.GET.get("max_budget")

    condition = (request.GET.get("condition") or "").strip()     # kept for UI parity (may be ignored if your models don’t support it)
    seller_type = (request.GET.get("seller_type") or "").strip()
    time_hours = (request.GET.get("time") or "").strip()
    sort = (request.GET.get("sort") or "").strip()

    # Featured (independent)
    featured_requests = (
        Request.objects.filter(
            listing__type="request",
            listing__is_approved=True,
            listing__is_active=True,
            listing__featured_until__gt=now,
        )
        .select_related("listing", "listing__category", "listing__city", "listing__user")
        .order_by("-listing__featured_until", "-listing__created_at")[:12]
    )

    base_qs = Request.objects.filter(
        listing__type="request",
        listing__is_approved=True,
        listing__is_active=True,
    ).select_related(
        "listing", "listing__user", "listing__category", "listing__city"
    )

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

    # Budget range (Request.budget)
    if min_budget:
        try:
            base_qs = base_qs.filter(budget__gte=float(min_budget))
        except ValueError:
            pass
    if max_budget:
        try:
            base_qs = base_qs.filter(budget__lte=float(max_budget))
        except ValueError:
            pass

    # seller type (store/individual)
    if seller_type:
        # if you have Store model like in items
        try:
            from .models import Store  # adjust import if needed
        except Exception:
            Store = None

        if Store is not None:
            if seller_type == "store":
                base_qs = base_qs.filter(listing__user__store__isnull=False)
            elif seller_type == "individual":
                base_qs = base_qs.filter(listing__user__store__isnull=True)

    # time window
    if time_hours:
        try:
            hours = int(time_hours)
            since = now - timedelta(hours=hours)
            base_qs = base_qs.filter(listing__created_at__gte=since)
        except ValueError:
            pass

    # search
    if len(q) >= 2:
        base_qs = base_qs.filter(
            Q(listing__title__icontains=q) | Q(listing__description__icontains=q)
        )

    # sort
    if sort == "budgetAsc":
        queryset = base_qs.order_by("budget", "-listing__created_at")
    elif sort == "budgetDesc":
        queryset = base_qs.order_by("-budget", "-listing__created_at")
    else:
        queryset = base_qs.order_by("-listing__created_at")

    PAGE_SIZE = 27
    paginator = Paginator(queryset, PAGE_SIZE)
    page_number = request.GET.get("page") or "1"
    page_obj = paginator.get_page(page_number)

    total_count = paginator.count
    visible_count = page_obj.end_index() if total_count else 0
    has_more = page_obj.has_next()

    categories = Category.objects.filter(parent__isnull=True).prefetch_related("subcategories").distinct()
    cities = City.objects.all().order_by("name_ar")

    # banners (same behavior as items; if you already provide banners elsewhere, keep it)
    banners = []
    try:
        from .models import Banner  # adjust if your banner model is named differently
        banners = Banner.objects.filter(is_active=True).order_by("-id")[:3]
    except Exception:
        banners = []

    context = {
        "page_obj": page_obj,
        "requests": page_obj.object_list,
        "q": q,
        "selected_category": selected_category,
        "categories": categories,
        "cities": cities,
        "selected_categories": request.GET.getlist("categories"),
        "total_count": total_count,
        "visible_count": visible_count,
        "featured_requests": featured_requests,
        "has_more": has_more,
        "banners": banners,
        "filters": {
            "category": category_id_single or "",
            "city": city_id or "",
            "condition": condition,
            "seller_type": seller_type,
            "time": time_hours,
            "sort": sort or "latest",
            "min_budget": min_budget,
            "max_budget": max_budget,
        }
    }

    is_hx = bool(request.headers.get("HX-Request"))
    is_xhr = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_hx:
        html = render_to_string("partials/request_results.html", context, request=request)
        return HttpResponse(html)

    if is_xhr:
        html = render_to_string("partials/request_results.html", context, request=request)
        return JsonResponse({
            "html": html,
            "total_count": total_count,
            "visible_count": visible_count,
            "has_more": has_more,
        })

    return render(request, "request_list.html", context)


# Item details
# ============================
#     ITEM DETAIL VIEW
# ============================
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    breadcrumb_categories = []
    cat = getattr(item.listing, "category", None)

    # Walk up to the root
    while cat:
        breadcrumb_categories.append(cat)
        cat = cat.parent

    breadcrumb_categories.reverse()  # root -> leaf

    attributes = []
    for av in item.attribute_values.select_related("attribute").prefetch_related("attribute__options"):
        attr = av.attribute
        value = av.value

        if attr.input_type == "select" and value:
            option = None
            try:
                option_id = int(value)  # ✅ only if it's a real option id
                option = attr.options.filter(id=option_id).first()
            except (TypeError, ValueError):
                option = None  # ✅ "Other" text

            if option:
                value = option.value_ar  # or value_en depending on language
            # else: keep typed text as-is

        attributes.append({
            "name": attr.name_ar,
            "value": value,
        })


    # ----------------------------
    # 1. Django fallback function
    # ----------------------------
    def fallback_similar():
        return (
            Item.objects.filter(
                listing__category=item.listing.category,
                listing__is_approved=True,
                listing__is_active=True,
            )
            .exclude(id=item.id)
            .order_by('-listing__created_at')[:6]
        )

    # Default → fallback queryset
    similar_items = fallback_similar()

    # Only try ES if NOT on Render
    if not getattr(settings, "IS_RENDER", False):
        try:
            es = Elasticsearch(settings.ELASTICSEARCH_DSL['default']['hosts'])

            query = {
                "query": {
                    "more_like_this": {
                        "fields": ["title", "description"],
                        "like": [{"_index": "items", "_id": item.id}],
                        "min_term_freq": 1,
                        "max_query_terms": 12,
                    }
                },
                "size": 6,
            }

            # --- IMPORTANT ---
            # This is the line that raises NotFoundError when index = "items" does not exist
            response = es.search(index="items", body=query)

            hits = response.get("hits", {}).get("hits", [])
            ids = [hit["_id"] for hit in hits]

            # If ES returned valid hits → get Django queryset
            if ids:
                es_items = (
                    Item.objects.filter(
                        id__in=ids,
                        listing__is_approved=True,
                        listing__is_active=True,
                    )
                    .exclude(id=item.id)
                    .order_by('-created_at')[:6]
                )

                if es_items.exists():
                    similar_items = es_items

        # ===============================
        # FULL protection from all errors
        # ===============================
        except (ConnectionError, NotFoundError, Exception) as e:
            print("[WARN] Elasticsearch error in item_detail:", e)
            # Keep fallback_similar()

    # ----------------------------
    # Is Favorite
    # ----------------------------
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, listing=item.listing).exists()


    seller = item.listing.user

    # ✅ CONTACT PRIVACY (NO PHONE LEAK)
    raw_phone = (seller.phone or "").strip()

    # masked (first 2 digits)
    seller_phone_masked = "07•• ••• •••"
    if raw_phone:
        first2 = raw_phone[:2] if len(raw_phone) >= 2 else raw_phone
        seller_phone_masked = f"{first2}•• ••• •••"

    # only send full phone if:
    # - seller allows showing phone
    # - viewer is authenticated
    can_send_full_phone = bool(item.listing.show_phone) and request.user.is_authenticated
    seller_phone_full = raw_phone if can_send_full_phone else ""

    # True if the seller has a Store row (OneToOne)
    seller_is_store = hasattr(seller, "store") and seller.store is not None
    store = seller.store if seller_is_store else None

    # verified flag (use is_verified or is_approved depending on your model)
    seller_is_verified_store = bool(store and getattr(store, "is_verified", False))
    # if you still have is_approved, use this instead:
    # seller_is_verified_store = bool(store and getattr(store, "is_approved", False))

    # Reviews: show ONLY for store users (verified or not — your choice)
    reviews = []
    if seller_is_store:
        # if your Review model related_name is "reviews" on Store
        reviews = store.reviews.select_related("reviewer").order_by("-created_at")[:10]

    seller_reviews_count = len(reviews)

    # Seller items count (same as you already do)
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

    # ----------------------------
    # Final render
    # ----------------------------
    return render(request, 'item_detail.html', {
        'item': item,
        'attributes': attributes,
        'similar_items': similar_items,
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


def request_detail(request, request_id):
    request_obj = get_object_or_404(Request, id=request_id)

    breadcrumb_categories = []
    cat = getattr(request_obj.listing, "category", None)

    while cat:
        breadcrumb_categories.append(cat)
        cat = cat.parent

    breadcrumb_categories.reverse()

    # SECURITY
    if not request_obj.listing.is_approved and request.user != request_obj.listing.user:
        if not request.user.is_staff:
            return redirect("home")

    attributes = []
    for av in request_obj.attribute_values.select_related("attribute").prefetch_related("attribute__options"):
        attr = av.attribute
        value = av.value

        # Dropdown / select attribute → normally value is an option ID
        if attr.input_type == "select" and value:
            option = None
            try:
                option_id = int(value)  # ✅ only works if it's a real option id
                option = attr.options.filter(id=option_id).first()
            except (TypeError, ValueError):
                option = None  # ✅ means it's "Other" text like "Test other"

            if option:
                value = option.value_ar  # or value_en if you want based on language
            # else: keep value as-is (the typed "Other" text)

        attributes.append({
            "name": attr.name_ar,
            "value": value,
        })


    # Similar requests (fallback like items)
    similar_requests = (
        Request.objects.filter(
            listing__category=request_obj.listing.category,
            listing__is_approved=True,
            listing__is_active=True,
        )
        .exclude(id=request_obj.id)
        .order_by("-listing__created_at")[:8]
    )

    requester = request_obj.listing.user

    # ✅ Only send full phone if allowed
    can_send_full_phone = bool(request_obj.listing.show_phone) and request.user.is_authenticated
    requester_phone_full = (requester.phone or "").strip() if can_send_full_phone else ""

    # Mask phone (show FIRST 2 digits)
    raw_phone = (requester.phone or "").strip()

    masked = "07•• ••• •••"  # fallback if empty (adjust if you prefer)
    if raw_phone:
        first2 = raw_phone[:2] if len(raw_phone) >= 2 else raw_phone
        masked = f"{first2}•• ••• •••"

    u = request_obj.listing.user

    requester_requests_count = Request.objects.filter(listing__user=u).count()

    reported_already = False
    if request.user.is_authenticated:
        reported_already = IssuesReport.objects.filter(
            user=request.user,
            target_kind="listing",
            listing=request_obj.listing,
            listing_type="request",
        ).exists()

    is_own_listing = False
    if request.user.is_authenticated:
        is_own_listing = (request_obj.listing.user_id == request.user.user_id)

    return render(
        request,
        "request_detail.html",
        {
            "request_obj": request_obj,
            "attributes": attributes,
            "similar_requests": similar_requests,

            # contact UI
            "requester_phone_masked": masked,
            "requester_phone_full": requester_phone_full,   # ✅ NEW (safe)
            "requester_requests_count": requester_requests_count,
            "allow_show_phone": request_obj.listing.show_phone,

            "report_kind": "request",
            "reported_already": reported_already,
            "breadcrumb_categories": breadcrumb_categories,
            "is_own_listing": is_own_listing,
        },
    )



# Only logged-in users can post
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

    # =============================
    # POST (Submit Ad)
    # =============================
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

            # -----------------------------
            # 3. Create ITEM (1-to-1)
            # -----------------------------
            item = Item.objects.create(
                listing=listing,
                price=form.cleaned_data["price"],
                condition=form.cleaned_data["condition"],
            )

            # -----------------------------
            # 4. Save uploaded images
            # -----------------------------
            images = request.FILES.getlist("images")
            main_index = request.POST.get("main_photo_index")
            main_index = int(main_index) if main_index and main_index.isdigit() else None

            for idx, img in enumerate(images):
                photo = ItemPhoto.objects.create(item=item, image=img)
                if main_index is not None and idx == main_index:
                    photo.is_main = True
                    photo.save()

            # Default main photo
            if images and not item.photos.filter(is_main=True).exists():
                first = item.photos.first()
                if first:
                    first.is_main = True
                    first.save()

            # -----------------------------
            # 5. ✅ Save dynamic attributes (FIXED)
            # -----------------------------
            for field_name, value in form.cleaned_data.items():

                # ✅ correct prefix for your dynamic fields
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

                # Multi-select types
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

                # Single-select types / text / number
                else:
                    if value == "__other__":
                        final_value = (form.cleaned_data.get(f"{field_name}_other") or "").strip()
                    else:
                        final_value = str(value).strip() if value is not None else ""

                # ✅ THIS was the bug in your project when you copied from request_create:
                # must save to ItemAttributeValue with item=item
                if final_value:
                    ItemAttributeValue.objects.create(
                        item=item,
                        attribute_id=attr_id,
                        value=final_value,
                    )

            # -----------------------------
            # 6. Notifications
            # -----------------------------
            for admin in User.objects.filter(is_staff=True):
                Notification.objects.create(
                    user=admin,
                    title="New item pending approval",
                    body=f"🕓 '{listing.title}' was posted by {request.user.username} and is awaiting approval.",
                    listing=listing,
                )

            Notification.objects.create(
                user=request.user,
                title="✅ إعلانك قيد المراجعة",
                body=f"تم استلام إعلانك '{listing.title}' وهو الآن بانتظار موافقة الإدارة.",
                listing=listing,
            )

            messages.success(request, "✅ Your ad was submitted (pending review).")
            return redirect("item_list")

        # -----------------------------
        # Form invalid
        # -----------------------------
        print("=== DEBUG: form is INVALID ===")
        print("form.errors:", form.errors.as_data())
        print("non_field_errors:", form.non_field_errors())
        print("cleaned_data:", getattr(form, "cleaned_data", {}))
        print("FILES images count:", len(request.FILES.getlist("images")))

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

    # =============================
    # GET request
    # =============================
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
def item_attributes_partial(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    # Empty form just to build attribute fields for that category
    form = ItemForm(category=category)
    return render(request, "partials/item_attributes.html", {"form": form})



@login_required
@transaction.atomic
def item_edit(request, item_id):
    # IMPORTANT: Item has NO user field → go through listing__user
    item = get_object_or_404(
        Item.objects.select_related("listing", "listing__category", "listing__user"),
        id=item_id,
        listing__user=request.user,
    )

    listing = item.listing
    category = listing.category

    # Initial data for non-model fields on the form
    initial = {
        "price": item.price,
        "condition": item.condition,
    }

    form = ItemForm(
        request.POST or None,
        request.FILES or None,
        category=category,
        initial=initial,
        instance=listing,  # ItemForm edits Listing
    )

    if request.method == "POST" and form.is_valid():
        # -----------------------------
        # 1. Save LISTING
        # -----------------------------
        listing = form.save(commit=False)
        listing.is_approved = False
        listing.was_edited = True
        listing.save()

        # -----------------------------
        # 2. Save ITEM-specific fields
        # -----------------------------
        item.price = form.cleaned_data.get("price")
        item.condition = form.cleaned_data.get("condition")
        item.save()

        # -----------------------------
        # 3. Delete removed photos
        # -----------------------------
        for key in request.POST:
            if key.startswith("delete_photo_"):
                try:
                    photo_id = int(key.split("_")[-1])
                except ValueError:
                    continue
                ItemPhoto.objects.filter(id=photo_id, item=item).delete()

        # -----------------------------
        # 4. Rebuild dynamic attributes
        # -----------------------------
        ItemAttributeValue.objects.filter(item=item).delete()

        # NOTE: ItemForm builds dynamic fields as "attr_<id>"
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

            # Multi-select types (checkbox/tags) come as list
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
                # Single choice
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

        # -----------------------------
        # 5. New photos + main photo
        # -----------------------------
        new_images = request.FILES.getlist("images")
        created_photos = [
            ItemPhoto.objects.create(item=item, image=img)
            for img in new_images
        ]

        selected_main_id = request.POST.get("selected_main_photo")
        main_index = request.POST.get("main_photo_index")
        main_index = int(main_index) if main_index and main_index.isdigit() else None

        # Reset all main flags
        ItemPhoto.objects.filter(item=item).update(is_main=False)

        # Priority 1: main existing photo chosen
        if selected_main_id:
            ItemPhoto.objects.filter(id=selected_main_id, item=item).update(is_main=True)

        # Priority 2: one of the newly uploaded photos (by index)
        elif main_index is not None and 0 <= main_index < len(created_photos):
            created_photos[main_index].is_main = True
            created_photos[main_index].save()

        # Priority 3: ensure some main photo exists
        elif not item.photos.filter(is_main=True).exists():
            first = item.photos.first()
            if first:
                first.is_main = True
                first.save()

        # -----------------------------
        # 6. Notifications
        # -----------------------------
        for admin in User.objects.filter(is_staff=True):
            Notification.objects.create(
                user=admin,
                title="Edited item pending approval",
                body=f"✏️ '{listing.title}' was edited by {request.user.username} and needs re-approval.",
                listing=listing,
            )

        Notification.objects.create(
            user=request.user,
            title="📋 إعلانك قيد المراجعة مجددًا",
            body=f"تم تعديل إعلانك '{listing.title}' وهو الآن بانتظار المراجعة من الإدارة.",
            listing=listing,
        )

        return redirect("item_detail", item_id=item.id)

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
@transaction.atomic
def request_create(request):
    # =============================
    # 1. Top-level categories
    # =============================
    lang = translation.get_language()
    order_field = "name_ar" if lang == "ar" else "name_en"

    top_categories = Category.objects.filter(parent__isnull=True).order_by(order_field)

    category_id = request.POST.get("category") or request.GET.get("category")
    selected_category = Category.objects.filter(id=category_id).first() if category_id else None

    # =============================
    # POST (Submit Request)
    # =============================
    if request.method == "POST":
        token = request.POST.get("form_token")
        session_token = request.session.get("item_create_form_token")

        if not token or token != session_token:
            return HttpResponseBadRequest("Duplicate or invalid submission")

        # consume token immediately to prevent double submit
        del request.session["item_create_form_token"]

        form = RequestForm(request.POST, category=selected_category)

        if form.is_valid() and selected_category:

            # -----------------------------
            # 2. Create LISTING
            # -----------------------------
            listing = form.save(commit=False)
            listing.category = selected_category
            listing.user = request.user
            listing.type = "request"
            listing.is_approved = False
            listing.is_active = True
            listing.show_phone = (request.POST.get("show_phone") == "on")
            listing.save()

            # -----------------------------
            # 3. Create REQUEST child
            # -----------------------------
            req = Request.objects.create(
                listing=listing,
                budget=form.cleaned_data.get("budget"),
                condition_preference=form.cleaned_data.get("condition_preference"),
            )

            # -----------------------------
            # 4. Save dynamic attributes
            # -----------------------------
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

                # Multi-select types
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

                # Single-select types
                else:
                    if value == "__other__":
                        final_value = form.cleaned_data.get(f"{field_name}_other", "").strip()
                    else:
                        final_value = str(value) if value is not None else ""

                if final_value:
                    RequestAttributeValue.objects.create(
                        request=req,
                        attribute_id=attr_id,
                        value=final_value,
                    )

            # -----------------------------
            # 5. Notifications
            # -----------------------------
            for admin in User.objects.filter(is_staff=True):
                Notification.objects.create(
                    user=admin,
                    title="New request pending approval",
                    body=f"🕓 '{listing.title}' was posted by {request.user.username} and is awaiting approval.",
                    listing=listing,
                )

            Notification.objects.create(
                user=request.user,
                title="✅ تم استلام طلبك",
                body=f"طلبك '{listing.title}' قيد المراجعة.",
                listing=listing,
            )

            messages.success(request, "✅ Your request was submitted (pending review).")
            return redirect("request_list")

        request.session["item_create_form_token"] = str(uuid.uuid4())

        # INVALID FORM
        return render(
            request,
            "request_create.html",
            {
                "form": form,
                "top_categories": top_categories,
                "categories": top_categories,
                "selected_category": selected_category,
                "form_token": request.session["item_create_form_token"],

            },
        )

    # =============================
    # GET request
    # =============================
    form = RequestForm(category=selected_category)

    category_tree = build_category_tree(top_categories, lang)
    category_tree_json = json.dumps(category_tree, ensure_ascii=False)

    selected_path = get_selected_category_path(selected_category)
    selected_path_json = json.dumps(selected_path)

    request.session["item_create_form_token"] = str(uuid.uuid4())


    return render(
        request,
        "request_create.html",
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



# Category form (simple)
class CategoryForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label="Parent Category",
        help_text="Optional — leave blank if this is a top-level category.",
    )

    class Meta:
        model = Category
        fields = ['name_en', 'name_ar', 'description', 'parent']


@staff_member_required
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category}" created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()

    return render(request, 'category_create.html', {'form': form})


# Optional: list categories (for admins)
@staff_member_required
def category_list(request):
    # Fetch all top-level categories (parent=None)
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')

    return render(request, 'category_list.html', {
        'categories': categories,
    })

# Form to create a new attribute for a category
class AttributeForm(forms.ModelForm):
    class Meta:
        model = Attribute
        fields = ['name_en', 'name_ar', 'input_type', 'is_required']

@staff_member_required
def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    attributes = category.attributes.all()

    attribute_form = AttributeForm()
    option_form = AttributeOptionForm()

    # Handle adding a new attribute
    if request.method == 'POST' and 'add_attribute' in request.POST:
        attribute_form = AttributeForm(request.POST)
        if attribute_form.is_valid():
            attr = attribute_form.save(commit=False)
            attr.category = category  # auto assign
            attr.save()
            messages.success(request, f"Attribute '{str(attr)}' added successfully!")
            return redirect('category_detail', category_id=category.id)

    # Handle adding a new option
    if request.method == 'POST' and 'add_option' in request.POST:
        attribute_id = request.POST.get('attribute_id')
        value_en = request.POST.get('value_en')
        value_ar = request.POST.get('value_ar')

        if attribute_id and value_en and value_ar:
            attribute = get_object_or_404(Attribute, id=attribute_id)
            AttributeOption.objects.create(
                attribute=attribute,
                value_en=value_en,
                value_ar=value_ar
            )
            messages.success(request, f"Option added to {str(attribute)}!")
            return redirect('category_detail', category_id=category.id)
        else:
            messages.error(request, "Please enter both English and Arabic values.")

    return render(request, 'category_detail.html', {
        'category': category,
        'attributes': attributes,
        'attribute_form': attribute_form,
        'option_form': option_form,
    })



class AttributeOptionForm(forms.ModelForm):
    class Meta:
        model = AttributeOption
        fields = ['value_en', 'value_ar', 'attribute']


@login_required
def start_conversation(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    listing = item.listing

    seller = listing.user
    buyer = request.user

    # don't allow messaging yourself
    if seller == buyer:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "self_message"}, status=400)
        return redirect("item_detail", item_id=item_id)

    convo = Conversation.objects.filter(listing=listing, buyer=buyer, seller=seller).first()
    if not convo:
        convo = Conversation.objects.create(listing=listing, buyer=buyer, seller=seller)

    # If not POST: just go to chat as before
    if request.method != "POST":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "conversation_id": convo.id})
        return redirect("chat_room", conversation_id=convo.id)

    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)

    # optional validation if you want
    try:
        validate_no_links_or_html(body)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "invalid"}, status=400)

    Message.objects.create(conversation=convo, sender=request.user, body=body)

    # ✅ IMPORTANT: AJAX returns JSON (NO redirect)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})

    # fallback old behavior
    return redirect("chat_room", conversation_id=convo.id)


@login_required
def start_conversation_request(request, request_id):
    req = get_object_or_404(Request, id=request_id)
    listing = req.listing

    # in your logic:
    seller = request.user       # helper
    buyer = listing.user        # requester

    if seller == buyer:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "self_message"}, status=400)
        return redirect("request_detail", request_id=request_id)

    convo = Conversation.objects.filter(listing=listing, buyer=buyer, seller=seller).first()
    if not convo:
        convo = Conversation.objects.create(listing=listing, buyer=buyer, seller=seller)

    if request.method != "POST":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "conversation_id": convo.id})
        return redirect("chat_room", conversation_id=convo.id)

    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)

    try:
        validate_no_links_or_html(body)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "invalid"}, status=400)

    Message.objects.create(conversation=convo, sender=request.user, body=body)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})

    return redirect("chat_room", conversation_id=convo.id)



@login_required
def chat_room(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        id=conversation_id
    )

    # SECURITY: Ensure user is part of the conversation
    if request.user not in [conversation.buyer, conversation.seller]:
        return redirect("item_list")

    listing = conversation.listing

    # The listing may be attached to an Item OR a Request (1-to-1)
    item = getattr(listing, "item", None)
    request_obj = getattr(listing, "request", None)

    # Mark unread messages (from the other user) as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    # SEND MESSAGE
    if request.method == "POST":
        body = request.POST.get("body", "").strip()

        if body:
            try:
                validate_no_links_or_html(body)
            except ValidationError:
                messages.error(request, "Links or HTML are not allowed in messages.")
            else:
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    body=body,
                )
                return redirect("chat_room", conversation_id=conversation_id)

    messages_qs = conversation.messages.select_related("sender").order_by("created_at")

    return render(
        request,
        "chat_room.html",
        {
            "conversation": conversation,
            "messages": messages_qs,
            "listing": listing,
            "item": item,
            "request_obj": request_obj,
        },
    )


@login_required
def user_inbox(request):
    convos = Conversation.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-created_at')

    return render(request, 'inbox.html', {
        'convos': convos
    })


@login_required
def item_edit(request, item_id):
    # Load item with listing and ensure ownership
    item = get_object_or_404(
        Item.objects.select_related("listing", "listing__category", "listing__user"),
        id=item_id,
        listing__user=request.user,
    )

    listing = item.listing
    category = listing.category

    # Initial values for listing + item + attributes
    initial = {
        "title": listing.title,
        "description": listing.description,
        "city": listing.city_id,
        "price": item.price,
        "condition": item.condition,
    }

    # Dynamic attributes -> must match "attr_<id>"
    attribute_initial = {
        f"attr_{av.attribute_id}": av.value
        for av in item.attribute_values.all()
    }
    initial.update(attribute_initial)

    form = ItemForm(
        request.POST or None,
        request.FILES or None,
        instance=listing,      # Model = Listing
        category=category,     # For dynamic attributes
        initial=initial,
    )

    if request.method == "POST" and form.is_valid():
        # Save listing fields
        listing = form.save(commit=False)
        listing.is_approved = False
        listing.was_edited = True
        listing.save()

        # Save item fields
        item.price = form.cleaned_data["price"]
        item.condition = form.cleaned_data["condition"]
        item.save()

        # Delete photos
        for key in request.POST:
            if key.startswith("delete_photo_"):
                pid = key.split("_")[-1]
                ItemPhoto.objects.filter(id=pid, item=item).delete()

        # Attributes
        ItemAttributeValue.objects.filter(item=item).delete()
        for key, value in request.POST.items():
            if key.startswith("attr_") and not key.endswith("_other"):
                try:
                    attr_id = int(key.split("_")[1])
                except ValueError:
                    continue

                if value == "__other__":
                    value = request.POST.get(f"{key}_other", "")

                value = value.strip()
                if value:
                    ItemAttributeValue.objects.create(
                        item=item,
                        attribute_id=attr_id,
                        value=value,
                    )

        # New photos
        new_images = request.FILES.getlist("images")
        created_photos = [
            ItemPhoto.objects.create(item=item, image=img)
            for img in new_images
        ]

        # Main photo logic
        selected_existing = request.POST.get("selected_main_photo")
        new_index = request.POST.get("main_photo_index")
        new_index = int(new_index) if new_index and new_index.isdigit() else None

        ItemPhoto.objects.filter(item=item).update(is_main=False)

        if selected_existing:
            ItemPhoto.objects.filter(id=selected_existing, item=item).update(is_main=True)
        elif new_index is not None and 0 <= new_index < len(created_photos):
            created_photos[new_index].is_main = True
            created_photos[new_index].save()
        else:
            first = item.photos.first()
            if first:
                first.is_main = True
                first.save()

        # Notifications
        for admin in User.objects.filter(is_staff=True):
            Notification.objects.create(
                user=admin,
                title="Edited item pending approval",
                body=f"✏️ '{listing.title}' was edited by {request.user.username}.",
                listing=listing,
            )

        Notification.objects.create(
            user=request.user,
            title="📋 إعلانك قيد المراجعة مجددًا",
            body=f"تم تعديل إعلانك '{listing.title}' وهو الآن بانتظار المراجعة.",
            listing=listing,
        )

        return redirect("item_detail", item_id=item.id)

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
def user_profile(request, user_id):
    User = get_user_model()

    seller = get_object_or_404(User, user_id=user_id)

    items = Item.objects.filter(
        user=seller,
        is_approved=True,
        is_active=True
    ).order_by('-created_at')

    return render(request, 'user_profile.html', {
        'seller': seller,
        'items': items,
    })


@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # mark unread as read
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications.html', {
        'notifications': notifications
    })


@login_required
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"success": True})


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
    item.delete()
    messages.success(request, "Item deleted successfully.")
    return redirect('my_items')


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



from django.http import JsonResponse

from django.http import JsonResponse

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



@login_required
def my_favorites(request):

    fav_qs = (
        Favorite.objects.filter(user=request.user)
        .select_related(
            "listing",
            "listing__item",
            "listing__item__user",
            "listing__item__category",
            "listing__item__city",
            "listing__request",
            "listing__request__user",
            "listing__request__category",
            "listing__request__city",
        )
        .prefetch_related("listing__item__photos")
        .order_by("-created_at")
    )

    # SPLIT THEM
    fav_items = [f for f in fav_qs if f.listing.type == "item"]
    fav_requests = [f for f in fav_qs if f.listing.type == "request"]

    # PAGINATION ONLY FOR ITEMS (requests usually few)
    paginator = Paginator(fav_items, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "fav_requests": fav_requests,
    }

    return render(request, "my_favorites.html", context)



@login_required
def edit_profile(request):
    """Allow user to edit their profile info (not username or phone)."""
    user = request.user
    if request.method == "POST":
        form = UserProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ تم تحديث معلوماتك بنجاح.")
            return redirect('user_profile', user.user_id)
        else:
            messages.error(request, "⚠️ يرجى تصحيح الأخطاء.")
    else:
        form = UserProfileEditForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form})


@login_required
def change_password(request):
    """Allow user to change password."""
    if request.method == "POST":
        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep logged in
            messages.success(request, "✅ تم تغيير كلمة المرور بنجاح.")
            return redirect('user_profile', request.user.user_id)
        else:
            messages.error(request, "⚠️ يرجى تصحيح الأخطاء.")
    else:
        form = UserPasswordChangeForm(user=request.user)

    return render(request, 'change_password.html', {'form': form})


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
        listing__is_active=True
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







def _category_descendant_ids(root):
    """Return [root.id] + all descendant category IDs (BFS)."""
    ids = []
    dq = deque([root])
    while dq:
        node = dq.popleft()
        ids.append(node.id)
        # requires Category(parent=..., related_name="subcategories")
        for child in node.subcategories.all():
            dq.append(child)
    return ids


def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            Subscriber.objects.get_or_create(email=email)
            messages.success(request, "✅ Thank you for subscribing!")
    return redirect('home')


def contact(request):
    return render(request, "contact.html")


@login_required
@require_POST
@csrf_protect
def create_issue_report_ajax(request):
    target_kind = (request.POST.get("target_kind") or "").strip()
    target_id = (request.POST.get("target_id") or "").strip()
    listing_type = (request.POST.get("listing_type") or "").strip()

    reason = (request.POST.get("reason") or "").strip()
    details = (request.POST.get("message") or "").strip()

    if target_kind not in ("listing", "user", "store"):
        return JsonResponse({"ok": False, "message": "Invalid target_kind."}, status=400)

    if not target_id.isdigit():
        return JsonResponse({"ok": False, "message": "Invalid target_id."}, status=400)

    if not reason:
        return JsonResponse({"ok": False, "message": "Please choose a reason."}, status=400)

    # reason is REQUIRED → always validate
    try:
        validate_no_links_or_html(reason)
    except ValidationError:
        return JsonResponse(
            {"ok": False, "message": "Links or HTML are not allowed."},
            status=400
        )

    # details is OPTIONAL → validate ONLY if provided
    if details:
        try:
            validate_no_links_or_html(details)
        except ValidationError:
            return JsonResponse(
                {"ok": False, "message": "Links or HTML are not allowed."},
                status=400
            )

    target_id_int = int(target_id)

    report = IssuesReport(
        user=request.user,
        target_kind=target_kind,
        reason=reason,
        message=details,
    )

    if target_kind == "listing":
        if listing_type not in ("item", "request"):
            return JsonResponse({"ok": False, "message": "Invalid listing_type."}, status=400)

        listing = get_object_or_404(Listing, id=target_id_int)

        # ✅ NEW: prevent reporting your own listing
        if listing.user_id == request.user.user_id:
            return JsonResponse(
                {"ok": False, "message": "لا يمكنك الإبلاغ عن إعلان/طلب قمت بإنشائه."},
                status=400
            )

        # ✅ BLOCK DUPLICATE REPORTS (same user + same listing + same listing_type)
        already = IssuesReport.objects.filter(
            user=request.user,
            target_kind="listing",
            listing=listing,
            listing_type=listing_type,
        ).exists()
        if already:
            return JsonResponse(
                {"ok": False, "message": "سبق أن قمت بالإبلاغ عن هذا المحتوى."},
                status=400
            )

        report.listing = listing
        report.listing_type = listing_type

    elif target_kind == "user":
        reported = get_object_or_404(User, id=target_id_int)
        report.reported_user = reported

        # optional: prevent reporting same user twice
        already = IssuesReport.objects.filter(
            user=request.user,
            target_kind="user",
            reported_user=reported,
        ).exists()
        if already:
            return JsonResponse({"ok": False, "message": "سبق أن قمت بالإبلاغ عن هذا المستخدم."}, status=400)

    else:  # store
        store = get_object_or_404(Store, id=target_id_int, is_active=True)

        # ✅ prevent reporting your own store
        if store.owner_id == request.user.user_id:
            return JsonResponse(
                {"ok": False, "message": "لا يمكنك الإبلاغ عن متجرك."},
                status=400
            )

        # ✅ block duplicates (same user + same store)
        already = IssuesReport.objects.filter(
            user=request.user,
            target_kind="store",
            store=store,
        ).exists()
        if already:
            return JsonResponse({"ok": False, "message": "سبق أن قمت بالإبلاغ عن هذا المتجر."}, status=400)

        report.store = store

    try:
        report.full_clean()
    except ValidationError:
        return JsonResponse({"ok": False, "message": "Invalid report data."}, status=400)

    report.save()
    return JsonResponse({"ok": True, "message": "✔ تم استلام الإبلاغ وسيتم مراجعته من فريق ركن"})

# from .forms import UserRegistrationForm


def register(request):
    """
    Render the SINGLE-PAGE mockup UI.
    (No user creation here.)
    """
    # capture referral if present
    ref_code = request.GET.get("ref")
    if ref_code:
        request.session["ref_code"] = ref_code

    form = UserRegistrationForm()
    return render(request, "register.html", {"form": form})


@require_POST
@csrf_protect
def ajax_send_signup_otp(request):
    """
    Mockup Step 1:
    - receive phone only
    - normalize
    - check not registered
    - send_code(...)
    - store pending phone in session
    """
    phone = (request.POST.get("phone") or "").strip().replace(" ", "").replace("-", "")

    # ✅ ONLY allow 07########
    if not re.fullmatch(r"07\d{8}", phone):
        return JsonResponse(
            {"ok": False, "error": "رقم الهاتف يجب أن يبدأ بـ 07 ويتكون من 10 أرقام. مثال: 0790000000"},
            status=400
        )

    # ✅ canonical format saved/used by OTP: 9627xxxxxxxx
    phone_norm = "962" + phone[1:]  # 9627xxxxxxxx

    # ✅ robust duplicate check (in case DB has old formats)
    local07 = phone  # 07xxxxxxxx
    plus = "+" + phone_norm  # +9627xxxxxxxx
    zerozero = "00" + phone_norm  # 009627xxxxxxxx

    if User.objects.filter(Q(phone=phone_norm) | Q(phone=local07) | Q(phone=plus) | Q(phone=zerozero)).exists():
        return JsonResponse(
            {"ok": False, "duplicated": True, "error": "هذا الرقم مسجَّل لدينا بالفعل."},
            status=409
        )

    request.session["pending_phone"] = phone_norm
    request.session["phone_verified_ok"] = False

    send_code(request, phone_norm, "verification", "verify", send_sms_code)
    return JsonResponse({"ok": True})


@require_POST
@csrf_protect
def ajax_verify_signup_otp(request):
    """
    Mockup Step 2 (popup):
    - verify code using verify_session_code
    - mark session verified
    """
    pending_phone = request.session.get("pending_phone")
    if not pending_phone:
        return JsonResponse({"ok": False, "error": "انتهت الجلسة. يرجى إعادة المحاولة."}, status=400)

    code = (request.POST.get("code") or "").strip()
    if not code:
        return JsonResponse({"ok": False, "error": "أدخل رمز التحقق."}, status=400)

    if not verify_session_code(request, "verification", code):
        return JsonResponse({"ok": False, "error": "⚠️ الرمز غير صحيح أو منتهي الصلاحية."}, status=400)

    request.session["phone_verified_ok"] = True
    return JsonResponse({"ok": True, "phone": pending_phone})


@csrf_protect
def complete_signup(request):
    if request.method != "POST":
        return redirect("register")

    pending_phone = request.session.get("pending_phone")
    verified_ok = request.session.get("phone_verified_ok", False)
    if not pending_phone or not verified_ok:
        messages.error(request, "يرجى تأكيد رقم الهاتف أولاً.")
        return redirect("register")

    # ✅ IMPORTANT for store_logo
    form = SignupAfterOtpForm(request.POST, request.FILES)

    if not form.is_valid():
        return render(request, "register.html", {
            "signup_form": form,
            "restore_step": "details",
            "verified_phone": pending_phone,
        })

    # safety re-check (handle old formats too)
    local07 = "0" + pending_phone[3:]     # 07xxxxxxxx
    plus = "+" + pending_phone            # +9627xxxxxxxx
    zerozero = "00" + pending_phone       # 009627xxxxxxxx

    if User.objects.filter(Q(phone=pending_phone) | Q(phone=local07) | Q(phone=plus) | Q(phone=zerozero)).exists():
        messages.error(request, "هذا الرقم مسجَّل لدينا بالفعل.")
        return redirect("register")

    with transaction.atomic():
        user = User.objects.create_user(
            phone=pending_phone,
            password=form.cleaned_data["password"],
        )

        user.first_name = form.cleaned_data.get("first_name", "") or ""
        user.last_name = form.cleaned_data.get("last_name", "") or ""
        user.is_active = True
        user.show_phone = True

        # ⚠️ only keep this if the field exists in your User model
        if hasattr(user, "phone_verified"):
            user.phone_verified = True

        if getattr(user, "date_joined", None) is None:
            user.date_joined = timezone.now()

        # referral
        ref_code = request.session.get("ref_code")
        if ref_code:
            try:
                referrer = User.objects.get(referral_code=ref_code)
                user.referred_by = referrer
            except User.DoesNotExist:
                pass

        user.save()

        print("POST condition:", request.POST.get("condition"))
        print("FILES keys:", list(request.FILES.keys()))

        # ✅ store creation
        if form.cleaned_data.get("condition") == "store":
            Store.objects.create(
                owner=user,
                name=form.cleaned_data.get("store_name", "").strip(),
                logo=form.cleaned_data.get("store_logo"),
            )

        if user.referred_by:
            user.referred_by.points += 50
            user.referred_by.save()

    # cleanup
    for key in ["pending_phone", "phone_verified_ok", "verification_code", "verification_sent_at", "ref_code"]:
        request.session.pop(key, None)

    login(request, user)
    messages.success(request, "✅ تم إنشاء الحساب بنجاح!")
    return redirect("home")


# ✅ Step 3: Forgot password – request code
def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                messages.error(request, "❌ رقم الهاتف غير موجود.")
                return redirect('forgot_password')

            # rate limit: 1 minute
            last_sent = request.session.get('reset_sent_at')
            if last_sent and timezone.now() - timezone.datetime.fromisoformat(last_sent) < timedelta(minutes=1):
                messages.warning(request, "⚠️ يرجى الانتظار دقيقة قبل طلب رمز جديد.")
                return redirect('forgot_password')

            send_code(request, phone, "reset", "reset", send_sms_code)
            request.session['reset_phone'] = phone
            messages.info(request, "📱 تم إرسال رمز التحقق إلى رقم هاتفك.")
            return redirect('verify_reset_code')
    else:
        form = ForgotPasswordForm()

    return render(request, 'forgot_password.html', {'form': form})


# ✅ Step 4: Verify code for password reset
def verify_reset_code(request):
    phone = request.session.get('reset_phone')
    if not phone:
        messages.error(request, "انتهت الجلسة. يرجى إعادة المحاولة.")
        return redirect('forgot_password')

    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['code']
            if verify_session_code(request, "reset", entered_code):
                request.session['reset_verified'] = True
                messages.success(request, "✅ تم التحقق من الرمز. يمكنك الآن تعيين كلمة مرور جديدة.")
                return redirect('reset_password')
            else:
                messages.error(request, "⚠️ الرمز غير صحيح أو منتهي الصلاحية.")
    else:
        form = PhoneVerificationForm()

    return render(request, 'verify_reset_code.html', {'form': form, 'phone': phone})


# ✅ Step 5: Reset password after verification
def reset_password(request):
    if not request.session.get('reset_verified'):
        messages.error(request, "يرجى التحقق من الرمز أولاً.")
        return redirect('forgot_password')

    phone = request.session.get('reset_phone')
    if not phone:
        messages.error(request, "حدث خطأ. يرجى إعادة المحاولة.")
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']

            if new_password != confirm_password:
                messages.error(request, "⚠️ كلمتا المرور غير متطابقتين.")
                return redirect('reset_password')

            try:
                user = User.objects.get(phone=phone)
                user.password = make_password(new_password)
                user.save()

                # clear session data
                for key in ['reset_phone', 'reset_code', 'reset_sent_at', 'reset_verified']:
                    request.session.pop(key, None)

                messages.success(request, "✅ تم تعيين كلمة المرور الجديدة بنجاح. يمكنك تسجيل الدخول الآن.")
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, "حدث خطأ. يرجى إعادة المحاولة.")
    else:
        form = ResetPasswordForm()

    return render(request, 'reset_password.html', {'form': form})



def _digits_only(s: str) -> str:
    return re.sub(r"\D+", "", (s or ""))


def _phone_candidates(raw: str) -> list[str]:
    d = _digits_only(raw)
    c = set()

    if d.startswith("07") and len(d) == 10:
        local07 = d
        norm962 = "962" + d[1:]
        c.update({local07, norm962, "+" + norm962, "00" + norm962})
        c.add(local07.lstrip("0"))  # legacy: 767xxxxxx

    elif d.startswith("9627") and len(d) == 12:
        norm962 = d
        local07 = "0" + d[3:]
        c.update({local07, norm962, "+" + norm962, "00" + norm962})
        c.add(local07.lstrip("0"))

    elif d.startswith("009627") and len(d) == 14:
        norm962 = d[2:]
        local07 = "0" + norm962[3:]
        c.update({local07, norm962, "+" + norm962, "00" + norm962})
        c.add(local07.lstrip("0"))

    else:
        return []

    c.discard("")
    return list(c)


def user_login(request):
    if request.method != "POST":
        return redirect("/")

    raw = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    referer = request.META.get("HTTP_REFERER", "/")
    next_url = (request.POST.get("next") or request.GET.get("next") or "").strip()

    def redirect_login_error():
        # keep next so after user fixes password, we still go to create page
        suffix = "?login_error=1"
        if next_url:
            suffix += f"&next={next_url}"
        return redirect(f"{referer}{suffix}")

    print("\n=== LOGIN ATTEMPT ===")
    print("raw:", repr(raw))

    candidates = _phone_candidates(raw)
    print("candidates:", candidates)

    if not candidates:
        print("INVALID INPUT FORMAT")
        return redirect_login_error()

    # Show exactly which phone value matched in DB
    matches = list(User.objects.filter(phone__in=candidates).values("pk", "phone")[:5])
    print("DB matches (pk, phone):", matches)

    u = User.objects.filter(phone__in=candidates).first()
    if not u:
        print("NO USER FOUND")
        return redirect_login_error()

    print("found pk:", u.pk)
    print("stored phone repr:", repr(getattr(u, "phone", None)))
    print("USERNAME_FIELD:", getattr(User, "USERNAME_FIELD", None))
    print("has_usable_password:", u.has_usable_password())

    # Authenticate using the model's USERNAME_FIELD (works for custom User models)
    login_key = User.USERNAME_FIELD
    login_val = getattr(u, login_key, None)
    print("auth using:", login_key, "=", repr(login_val))

    user = authenticate(request, password=password, **{login_key: login_val})
    print("authenticate() result:", user)

    if not user:
        print("AUTH FAILED (backend/USERNAME_FIELD mismatch, unusable password, or user created differently)")
        return redirect_login_error()

    login(request, user)
    print("LOGIN SUCCESS")

    # ✅ redirect to next (create item/request) if provided and safe
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)

    # fallback
    return redirect(referer)


# Logout
def user_logout(request):
    logout(request)
    return redirect('home')


from marketplace.services.promotions import buy_featured_with_points, NotEnoughPoints

@login_required
def feature_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id, user=request.user)

    DAYS = 7
    COST = 50  # set your business rule

    try:
        buy_featured_with_points(user=request.user, listing=listing, days=DAYS, points_cost=COST)
        messages.success(request, f"تم تمييز الإعلان لمدة {DAYS} أيام.")
    except NotEnoughPoints:
        messages.error(request, "رصيد النقاط غير كافٍ.")
    return redirect("profile")  # or listing detail


from django.db.models import F

def store_profile(request, store_id):
    store = get_object_or_404(Store, pk=store_id, is_active=True)

    # ✅ Increment views (logged-in + logged-out), once per session per store
    session_key = f"store_viewed_{store_id}"
    if not request.session.get(session_key):
        Store.objects.filter(pk=store.pk).update(views_count=F("views_count") + 1)
        request.session[session_key] = True
        store.refresh_from_db(fields=["views_count"])

    listings = (
        Listing.objects
        .filter(user=store.owner, is_active=True, is_approved=True, type="item")
        .select_related("category", "city", "user")
        .order_by("-created_at")[:30]
    )

    listings_count = Listing.objects.filter(
        user=store.owner, is_active=True, is_approved=True, type="item"
    ).count()

    def _root_category(cat):
        while cat and cat.parent_id:
            cat = cat.parent
        return cat

    for l in listings:
        # category is on the Listing attached to Item in your project
        cat = getattr(l.item, "listing", None)
        cat = getattr(cat, "category", None)
        root = _root_category(cat)
        l.root_category_id = root.id if root else ""

        city_id = getattr(l.item, "city_id", None)
        if not city_id:
            city_id = getattr(l, "city_id", None)

        l._city_id = city_id or ""

    categories = Category.objects.filter(parent__isnull=True).order_by("name_ar")
    cities = City.objects.filter(is_active=True).order_by("name_ar")

    # Reviews list (server-rendered list if you already show it)
    reviews = (
        StoreReview.objects
        .filter(store=store)
        .select_related("reviewer")
        .order_by("-created_at")
    )

    # follow state
    is_following = False
    if request.user.is_authenticated:
        is_following = StoreFollow.objects.filter(store=store, user=request.user).exists()

    # phone reveal
    full_phone = store.owner.phone if getattr(store.owner, "phone", None) else ""
    masked_phone = "07•• ••• •••"

    # ✅ user review (for prefill + edit after reload)
    user_review = None
    if request.user.is_authenticated:
        r = StoreReview.objects.filter(store=store, reviewer=request.user).first()
        if r:
            user_review = {
                "rating": int(r.rating or 0),
                "subject": r.subject or "",
                "comment": r.comment or "",
            }

    ctx = {
        "store": store,
        "listings": listings,
        "listings_count": listings_count,
        "categories": categories,
        "cities": cities,
        "reviews": reviews,
        "is_following": is_following,
        "full_phone": full_phone,
        "masked_phone": masked_phone,
        "user_review": user_review,  # dict or None
    }

    return render(request, "store_profile.html", ctx)

@login_required
@require_POST
def store_follow_toggle(request, store_id):
    store = get_object_or_404(Store, pk=store_id, is_active=True)

    session_key = f"store_viewed_{store_id}"
    if not request.session.get(session_key):
        Store.objects.filter(pk=store.pk).update(views_count=F("views_count") + 1)
        request.session[session_key] = True

        # refresh value in `store` object so template shows updated count
        store.refresh_from_db(fields=["views_count"])

    obj = StoreFollow.objects.filter(store=store, user=request.user).first()
    if obj:
        obj.delete()
        following = False
    else:
        StoreFollow.objects.create(store=store, user=request.user)
        following = True

    followers_count = StoreFollow.objects.filter(store=store).count()
    return JsonResponse({"ok": True, "following": following, "followers_count": followers_count})



@login_required
@require_POST
@csrf_protect
def submit_store_review_ajax(request, store_id):
    store = get_object_or_404(Store, id=store_id)

    rating = (request.POST.get("rating") or "").strip()
    subject = (request.POST.get("subject") or "").strip()
    comment = (request.POST.get("comment") or "").strip()

    try:
        rating_int = int(rating)
    except Exception:
        return JsonResponse({"ok": False, "message": "التقييم غير صالح."}, status=400)

    if rating_int < 1 or rating_int > 5:
        return JsonResponse({"ok": False, "message": "اختر تقييم من 1 إلى 5."}, status=400)

    obj, created = StoreReview.objects.update_or_create(
        store=store,
        reviewer=request.user,
        defaults={
            "rating": rating_int,
            "subject": subject,
            "comment": comment,
        },
    )

    recalc_store_rating(store.id)
    store.refresh_from_db()

    return JsonResponse({
        "ok": True,
        "message": "✔ تم حفظ تقييمك بنجاح",
        "created": created,

        # aggregates
        "rating_avg": float(store.rating_avg or 0),
        "rating_count": int(store.rating_count or 0),

        # ✅ return what we saved (so JS can update state without reload)
        "user_review": {
            "rating": int(obj.rating or 0),
            "subject": obj.subject or "",
            "comment": obj.comment or "",
        }
    })


def store_reviews_list(request, store_id):
    store = get_object_or_404(Store, pk=store_id, is_active=True)

    page = int(request.GET.get("page", "1") or 1)
    per_page = int(request.GET.get("per_page", "6") or 6)

    qs = StoreReview.objects.filter(store=store).select_related("reviewer").order_by("-created_at")
    paginator = Paginator(qs, per_page)
    p = paginator.get_page(page)

    breakdown = (
        qs.values("rating")
        .annotate(count=Count("id"))
        .order_by("-rating")
    )
    breakdown_map = {str(x["rating"]): x["count"] for x in breakdown}

    avg = qs.aggregate(avg=Avg("rating"))["avg"] or 0
    count = qs.count()

    data = {
        "ok": True,
        "avg": round(float(avg), 2),
        "count": count,
        "breakdown": breakdown_map,
        "page": p.number,
        "pages": paginator.num_pages,
        "results": [
            {
                "id": r.id,
                "rating": r.rating,
                "subject": r.subject or "",
                "comment": r.comment or "",
                "created_at": r.created_at.strftime("%Y-%m-%d"),
                "reviewer": getattr(r.reviewer, "username", "") or r.reviewer.phone,
                "is_user": (request.user.is_authenticated and r.reviewer_id == request.user.user_id),
            }
            for r in p.object_list
        ],
    }
    return JsonResponse(data)

