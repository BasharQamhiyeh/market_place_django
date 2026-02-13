from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, F, Count, Avg
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.db import IntegrityError

from marketplace.models import Store, Category, Listing, City, StoreReview, StoreFollow, IssuesReport
from marketplace.services.notifications import notify, K_STORE_FOLLOW, S_FOLLOWED, S_UNFOLLOWED
from marketplace.utils.service import recalc_store_rating


def stores_list(request):
    context = _stores_queryset_and_context(request)
    return render(request, "stores_list.html", context)


def stores_list_partial(request):
    if request.headers.get("HX-Request") != "true":
        # keep the same querystring
        qs = request.META.get("QUERY_STRING", "")
        url = reverse("stores_list")
        return redirect(f"{url}?{qs}" if qs else url)

    context = _stores_queryset_and_context(request)
    return render(request, "partials/stores_list_results.html", context)


def _stores_queryset_and_context(request):
    q = (request.GET.get("q") or "").strip()
    selected_categories = request.GET.getlist("categories")

    stores_qs = (
        Store.objects
        .filter(is_active=True)
        .select_related("owner", "city")
    )

    if q:
        stores_qs = stores_qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(specialty__icontains=q)
        )

    if selected_categories:
        stores_qs = stores_qs.filter(
            Q(owner__listings__category_id__in=selected_categories) |
            Q(owner__listings__category__parent_id__in=selected_categories),
            owner__listings__type="item",
            owner__listings__is_active=True,
            owner__listings__is_approved=True,
            owner__listings__is_deleted=False
        ).distinct()

    stores_qs = stores_qs.annotate(
        followers_count=Count("followers", distinct=True),
        ads_count=Count(
            "owner__listings",
            filter=Q(
                owner__listings__type="item",
                owner__listings__is_active=True,
                owner__listings__is_approved=True,
                owner__listings__is_deleted=False
            ),
            distinct=True
        )
    ).order_by("-rating_avg", "-rating_count", "-created_at")

    PAGE_SIZE = 12
    paginator = Paginator(stores_qs, PAGE_SIZE)
    page_number = request.GET.get("page") or "1"
    page_obj = paginator.get_page(page_number)

    categories = (
        Category.objects
        .filter(parent__isnull=True)
        .filter(
            Q(
                listings__type="item",
                listings__is_active=True,
                listings__is_approved=True,
                listings__is_deleted=False,
                listings__user__store__isnull=False,
                listings__user__store__is_active=True,
            )
            |
            Q(
                subcategories__listings__type="item",
                subcategories__listings__is_active=True,
                subcategories__listings__is_approved=True,
                subcategories__listings__is_deleted=False,
                subcategories__listings__user__store__isnull=False,
                subcategories__listings__user__store__is_active=True,
            )
        )
        .distinct()
        .order_by("name_ar")
    )

    total_count = paginator.count
    visible_count = page_obj.end_index() if total_count else 0
    has_more = page_obj.has_next()

    context = {
        "page_obj": page_obj,
        "stores": page_obj.object_list,
        "q": q,
        "categories": categories,
        "selected_categories": selected_categories,
        "total_count": total_count,
        "visible_count": visible_count,
        "has_more": has_more,
    }
    return context


def store_profile(request, store_id):
    store = get_object_or_404(Store, pk=store_id, is_active=True)

    session_key = f"store_viewed_{store_id}"
    if not request.session.get(session_key):
        Store.objects.filter(pk=store.pk).update(views_count=F("views_count") + 1)
        request.session[session_key] = True
        store.refresh_from_db(fields=["views_count"])

    base_qs = (
        Listing.objects
        .filter(user=store.owner, is_active=True, is_approved=True, type="item")
        .select_related("category", "city", "user")
        .order_by("-published_at")
    )

    listings = list(base_qs[:30])
    listings_count = base_qs.count()

    # --------- build root categories for chips (from ALL listings) ---------
    # Build parent map once (categories table usually small)
    cats = Category.objects.all().only("id", "parent_id", "name_ar", "name_en")
    parent_map = {c.id: c.parent_id for c in cats}

    def root_id(cat_id: int):
        cur = cat_id
        while cur and parent_map.get(cur):
            cur = parent_map[cur]
        return cur

    cat_ids = list(base_qs.exclude(category_id__isnull=True).values_list("category_id", flat=True).distinct())
    root_ids = sorted({root_id(cid) for cid in cat_ids if cid})

    store_categories = list(
        Category.objects.filter(id__in=root_ids, parent__isnull=True).order_by("name_ar")
    )

    # --------- attach filter data to the 30 rendered cards (NO extra DB hits) ---------
    for l in listings:
        # ✅ category is on Listing (you already select_related("category"))
        cat = getattr(l, "category", None)
        rid = root_id(cat.id) if cat else ""
        l.root_category_id = rid or ""

        # city id (prefer item.city_id if exists, else listing city)
        city_id = getattr(l.item, "city_id", None) or getattr(l, "city_id", None) or ""
        l._city_id = city_id

    categories = Category.objects.filter(parent__isnull=True).order_by("name_ar")
    cities = City.objects.filter(is_active=True).order_by("name_ar")

    reviews = (
        StoreReview.objects
        .filter(store=store)
        .select_related("reviewer")
        .order_by("-created_at")
    )

    is_following = False
    if request.user.is_authenticated:
        is_following = StoreFollow.objects.filter(store=store, user=request.user).exists()

    # phone reveal (respect store + user privacy flags)
    is_auth = request.user.is_authenticated
    allow_show_phone = bool(getattr(store, "show_phone", True)) and bool(getattr(store.owner, "show_phone", True))

    seller_phone_full = store.owner.phone if (allow_show_phone and getattr(store.owner, "phone", None)) else ""
    seller_phone_masked = "07•• ••• •••"

    user_review = None
    if request.user.is_authenticated:
        r = StoreReview.objects.filter(store=store, reviewer=request.user).first()
        if r:
            user_review = {
                "rating": int(r.rating or 0),
                "subject": r.subject or "",
                "comment": r.comment or "",
            }

    followers_count = StoreFollow.objects.filter(store=store).count()

    reported_already = False
    is_own_store = False
    if request.user.is_authenticated:
        is_own_store = (store.owner_id == request.user.user_id)
        reported_already = IssuesReport.objects.filter(
            user=request.user,
            target_kind="store",
            store=store,
        ).exists()

    PM_LABELS = {"cash": "كاش", "card": "بطاقة", "cliq": "CliQ", "transfer": "تحويل"}
    pm = store.payment_methods or []
    payment_text = " / ".join(PM_LABELS[k] for k in pm if k in PM_LABELS) or "غير محدد"

    ctx = {
        "store": store,
        "listings": listings,
        "listings_count": listings_count,
        "categories": categories,
        "cities": cities,
        "reviews": reviews,
        "allow_show_phone": allow_show_phone,
        "seller_phone_full": seller_phone_full,
        "seller_phone_masked": seller_phone_masked,
        "user_review": user_review,
        "is_following": is_following,
        "followers_count": followers_count,
        "reported_already": reported_already,
        "is_own_store": is_own_store,

        # ✅ new: chips data
        "store_categories": store_categories,
        "store_payment_text": payment_text
    }

    return render(request, "store_profile.html", ctx)


@login_required
@require_POST
def store_follow_toggle(request, store_id):
    store = get_object_or_404(Store, pk=store_id, is_active=True)

    # ✅ block self-follow
    if store.owner_id == request.user.user_id:
        return JsonResponse(
            {"ok": False, "error": "self_follow_not_allowed"},
            status=400
        )

    # toggle
    existing = StoreFollow.objects.filter(store=store, user=request.user).first()
    if existing:
        existing.delete()
        following = False
    else:
        try:
            StoreFollow.objects.create(store=store, user=request.user)
            following = True
        except IntegrityError:
            # unique constraint race condition (double click / multi requests)
            following = True

    # notify store owner (no self)

    if store.owner_id != request.user.user_id:
        if following:
            notify(
                user=store.owner,
                kind=K_STORE_FOLLOW,
                status=S_FOLLOWED,
                title="تمت متابعة متجرك",
                body="قام أحد المستخدمين بمتابعة متجرك وسيصله كل جديد من إعلاناتك.",
            )
        else:
            notify(
                user=store.owner,
                kind=K_STORE_FOLLOW,
                status=S_UNFOLLOWED,
                title="تم إلغاء متابعة متجرك",
                body="قام أحد المستخدمين بإلغاء متابعة متجرك.",
            )

    followers_count = StoreFollow.objects.filter(store=store).count()

    return JsonResponse({
        "ok": True,
        "following": following,
        "followers_count": followers_count,
    })


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

    qs = (
        StoreReview.objects
        .filter(store=store)
        .select_related("reviewer")
        .order_by("-created_at")
    )

    paginator = Paginator(qs, per_page)
    p = paginator.get_page(page)

    breakdown = qs.values("rating").annotate(count=Count("id")).order_by("-rating")
    breakdown_map = {str(x["rating"]): x["count"] for x in breakdown}

    avg = qs.aggregate(avg=Avg("rating"))["avg"] or 0
    count = qs.count()

    def get_display_name(user):
        if not user:
            return "مستخدم"
        username = (getattr(user, "username", "") or "").strip()
        first_name = (getattr(user, "first_name", "") or "").strip()
        phone = (getattr(user, "phone", "") or "").strip()
        return username or first_name or phone or "مستخدم"

    def get_avatar_url(user):
        """
        Adjust the field list below to match your actual User image field name.
        Common ones: avatar, photo, profile_photo, image, profile_image
        """
        if not user:
            return ""

        for field in ("avatar", "photo", "profile_photo", "image", "profile_image", "picture"):
            f = getattr(user, field, None)
            try:
                if f and getattr(f, "url", None):
                    # make it absolute so JS can use it directly
                    return request.build_absolute_uri(f.url)
            except Exception:
                pass

        return ""

    # your custom user PK might be user_id
    current_uid = getattr(request.user, "user_id", None) if request.user.is_authenticated else None
    if current_uid is None and request.user.is_authenticated:
        current_uid = request.user.id

    results = []
    for r in p.object_list:
        u = getattr(r, "reviewer", None)
        reviewer_id = getattr(r, "reviewer_id", None)

        results.append({
            "id": r.id,
            "rating": r.rating,
            "subject": r.subject or "",
            "comment": r.comment or "",
            "created_at": r.created_at.strftime("%Y-%m-%d"),

            # ✅ frontend will use this for name + initials
            "reviewer": get_display_name(u),

            # ✅ if exists -> photo will show; else "" -> JS shows initial letter
            "avatar": get_avatar_url(u),

            "is_user": (current_uid is not None and reviewer_id == current_uid),
        })

    data = {
        "ok": True,
        "avg": round(float(avg), 2),
        "count": count,
        "breakdown": breakdown_map,
        "page": p.number,
        "pages": paginator.num_pages,
        "results": results,
    }
    return JsonResponse(data)