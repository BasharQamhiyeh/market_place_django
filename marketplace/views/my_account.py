from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError
from django.contrib import messages

from marketplace.forms import UserProfileEditForm, UserPasswordChangeForm
from marketplace.models import Favorite, Item, Request, Notification
from marketplace.views.constants import ALLOWED_PAYMENT_METHODS, ALLOWED_DELIVERY, ALLOWED_RETURN
from marketplace.views.helpers import _fmt_date, _status_from_listing, translate_condition, normalize_optional_url


@require_GET
@login_required
def my_account(request: HttpRequest):
    Favorite.objects.filter(listing__type="item", listing__item__isnull=True).delete()

    user = request.user
    store = getattr(user, "store", None)
    has_store = bool(store) and getattr(store, "is_active", True)

    today = timezone.localdate()

    def _days_left(dt_or_date):
        """
        Returns positive integer days left from today; 0 if expired/none.
        Works with date or datetime.
        """
        if not dt_or_date:
            return 0
        end = dt_or_date.date() if hasattr(dt_or_date, "date") else dt_or_date
        diff = (end - today).days
        return diff if diff > 0 else 0

    # -------------------------
    # ADS (Listings type="item")
    # -------------------------
    ads_qs = (
        Item.objects
        .filter(listing__user=user, listing__type="item", listing__is_active=True, listing__is_deleted=False)
        .select_related("listing__category", "listing__city", "listing")
        .prefetch_related("photos")
        .order_by("-listing__published_at")
    )

    my_ads = []
    for it in ads_qs:
        listing = it.listing

        image_url = ""
        p = getattr(it, "main_photo", None)
        if p:
            image_url = (p.normalized.url if getattr(p, "normalized", None) else p.image.url)

        featured_until = getattr(listing, "featured_until", None)

        my_ads.append({
            # ids / text
            "id": it.id,
            "listing_id": listing.id,
            "title": listing.title or "",

            # money
            "price": float(it.price) if it.price is not None else None,

            # meta
            "city": str(listing.city) if listing.city else "",
            "created_at": _fmt_date(getattr(listing, "created_at", None)),
            "published_at": _fmt_date(getattr(listing, "published_at", None)),

            # stats (keep as-is)
            "views": getattr(listing, "views_count", 0) or 0,
            "favCount": Favorite.objects.filter(listing=listing).count(),

            # media
            "image": image_url,

            # moderation/status
            "status": _status_from_listing(listing),
            "category": str(listing.category) if listing.category else "بدون قسم",
            "rejectReason": getattr(listing, "moderation_reason", "") or "",

            # featured
            "featured": bool(getattr(listing, "is_featured", False)),
            "featuredExpiresAt": _fmt_date(featured_until),
            "featuredDaysLeft": _days_left(featured_until),

            # urls (fill later if you want)
            "editUrl": "",
            "detailUrl": "",
        })

    # -------------------------
    # REQUESTS (Listings type="request")
    # -------------------------
    req_qs = (
        Request.objects
        .filter(listing__user=user, listing__type="request", listing__is_deleted=False)
        .select_related("listing__category", "listing__city", "listing")
        .order_by("-listing__published_at")
    )

    my_requests = []
    for req in req_qs:
        listing = req.listing

        # your project seems inconsistent: sometimes featured_until vs featured_expires_at
        featured_expires = getattr(listing, "featured_expires_at", None) or getattr(listing, "featured_until", None)

        my_requests.append({
            # ids / text
            "id": req.id,
            "listing_id": req.listing.id,
            "title": (getattr(req, "title", "") or getattr(listing, "title", "") or ""),

            # money
            "budget": float(getattr(req, "budget", 0) or 0),

            # meta
            "city": getattr(getattr(listing, "city", None), "name", "") or str(getattr(listing, "city", "") or ""),
            "condition": translate_condition(getattr(req, "condition_preference", "")),
            "created_at": _fmt_date(getattr(listing, "created_at", None)),
            "published_at": _fmt_date(getattr(listing, "published_at", None)),

            "views": getattr(listing, "views_count", 0) or 0,

            # moderation/status
            "status": _status_from_listing(listing),
            "category": getattr(getattr(listing, "category", None), "name", "") or str(getattr(listing, "category", "") or "") or "ركن الطلبات",
            "rejectReason": (
                getattr(listing, "reject_reason", "") or
                getattr(listing, "moderation_reason", "") or
                ""
            ),

            # featured
            "featured": bool(getattr(listing, "is_featured", False)),
            "featuredExpiresAt": _fmt_date(featured_expires),
            "featuredDaysLeft": _days_left(featured_expires),

            "lastRepublishAt": _fmt_date(getattr(listing, "last_republish_at", None)),

            # urls
            "editUrl": (req.get_edit_url() if hasattr(req, "get_edit_url") else ""),
            "detailUrl": (req.get_absolute_url() if hasattr(req, "get_absolute_url") else ""),
        })

    # Favorites (items only) for the favorites tab
    fav_qs = (
        Favorite.objects
        .filter(user=request.user, listing__type="item")
        .select_related(
            "listing",
            "listing__user",
            "listing__category",
            "listing__city",
            "listing__item",
        )
        .prefetch_related("listing__item__photos")
        .order_by("-created_at")
    )

    paginator = Paginator(fav_qs, 12)
    fav_page_number = request.GET.get("fav_page")
    fav_page_obj = paginator.get_page(fav_page_number)

    # Items for the card
    fav_items_on_page = []
    for fav in fav_page_obj.object_list:
        item = getattr(fav.listing, "item", None)  # safe
        if not item:
            continue  # skip broken favorite (or collect to clean later)

        item.is_favorited = True
        fav_items_on_page.append(item)

    fav_count = paginator.count


    return render(
        request,
        "my_account/my_account.html",
        {
            "me": user,
            "store": store,
            "has_store": has_store,
            "my_ads": my_ads,
            "my_requests": my_requests,
            "fav_items": fav_items_on_page,
            "fav_count": fav_count,
            "fav_page_obj": fav_page_obj,
        },
    )


@require_POST
@login_required
@csrf_protect
def my_account_save_info(request: HttpRequest):
    user = request.user
    store = getattr(user, "store", None)

    # -----------------------
    # User fields
    # -----------------------
    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()
    username = (request.POST.get("username") or "").strip() or None
    email = (request.POST.get("email") or "").strip() or None

    if not first_name:
        return JsonResponse({"ok": False, "errors": {"first_name": ["الاسم الأول مطلوب."]}}, status=400)
    if not last_name:
        return JsonResponse({"ok": False, "errors": {"last_name": ["الاسم الأخير مطلوب."]}}, status=400)

    user.first_name = first_name
    user.last_name = last_name

    # username uniqueness handled by full_clean
    if username != user.username:
        user.username = username

    if email != user.email:
        user.email = email

    # -----------------------
    # Avatar (same endpoint)
    # -----------------------
    remove_profile = (request.POST.get("remove_profile_photo") or "") == "1"
    profile_file = request.FILES.get("profile_photo")

    if hasattr(user, "profile_photo"):
        if remove_profile:
            if user.profile_photo:
                user.profile_photo.delete(save=False)
            user.profile_photo = None
        elif profile_file:
            if user.profile_photo:
                user.profile_photo.delete(save=False)
            user.profile_photo = profile_file

    # Validate + save user
    try:
        user.full_clean()
        user.save()
    except ValidationError as e:
        return JsonResponse({"ok": False, "errors": e.message_dict}, status=400)

    profile_photo_url = None
    if hasattr(user, "profile_photo") and user.profile_photo:
        try:
            profile_photo_url = user.profile_photo.url
        except Exception:
            profile_photo_url = None

    # -----------------------
    # Store fields (only if store exists)
    # -----------------------
    store_logo_url = None

    if store:
        store_name = (request.POST.get("store_name") or "").strip()

        # ✅ accept either key
        store_desc = (
                (request.POST.get("store_desc") or "").strip()
                or (request.POST.get("store_description") or "").strip()
        )

        store_specialty = (request.POST.get("store_specialty") or "").strip()

        store_website = normalize_optional_url(request.POST.get("store_website"))
        store_instagram = normalize_optional_url(request.POST.get("store_instagram"))
        store_facebook = normalize_optional_url(request.POST.get("store_facebook"))

        store_whatsapp = (request.POST.get("store_whatsapp") or "").strip()
        store_city_id = (request.POST.get("store_city_id") or "").strip()
        store_address = (request.POST.get("store_address") or "").strip()

        # ✅ NEW: phone visibility (yes/no)
        show_mobile = (request.POST.get("show_mobile") or "").strip().lower()
        # default: True (show phone)
        store.show_phone = (show_mobile != "no") if show_mobile else store.show_phone

        # ✅ NEW: payment methods (multi)
        pm = request.POST.getlist("payment_methods")
        pm_clean = [p for p in pm if p in ALLOWED_PAYMENT_METHODS]
        store.payment_methods = pm_clean

        # ✅ NEW: delivery + return
        delivery = (request.POST.get("delivery_time") or "").strip()
        store.delivery_policy = delivery if delivery in ALLOWED_DELIVERY else ""

        ret = (request.POST.get("return_policy") or "").strip()
        store.return_policy = ret if ret in ALLOWED_RETURN else ""

        # ✅ validate on SAVE (not DB required)
        errors = {}
        if not store_name:
            errors["store_name"] = ["اسم المتجر مطلوب."]

        # only validate these when store form exists (it does if store exists)
        if not store_specialty:
            errors["store_specialty"] = ["تخصص المتجر مطلوب."]
        if not store_desc:
            errors["store_description"] = ["وصف المتجر مطلوب."]

        # group validations
        if not show_mobile:
            errors["show_mobile"] = ["الرجاء تحديد إعدادات عرض رقم الهاتف."]

        if not pm_clean:
            errors["payment_methods"] = ["الرجاء اختيار طريقة دفع واحدة على الأقل."]

        if not store.delivery_policy:
            errors["delivery_time"] = ["الرجاء اختيار سياسة التوصيل."]

        if not store.return_policy:
            errors["return_policy"] = ["الرجاء اختيار سياسة الإرجاع."]

        if errors:
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        # save store basic
        store.name = store_name
        store.description = store_desc
        store.specialty = store_specialty

        store.website = store_website
        store.instagram = store_instagram
        store.facebook = store_facebook
        store.whatsapp = store_whatsapp

        # city
        if store_city_id:
            try:
                store.city_id = int(store_city_id)
            except ValueError:
                store.city_id = None
        else:
            store.city_id = None

        store.address = store_address

        # logo
        remove_logo = (request.POST.get("remove_store_logo") or "") == "1"
        logo_file = request.FILES.get("store_logo")

        if remove_logo:
            if store.logo:
                store.logo.delete(save=False)
            store.logo = None
        elif logo_file:
            if store.logo:
                store.logo.delete(save=False)
            store.logo = logo_file

        try:
            store.full_clean()
            store.save()
        except ValidationError as e:
            return JsonResponse({"ok": False, "errors": e.message_dict}, status=400)

        if store.logo:
            try:
                store_logo_url = store.logo.url
            except Exception:
                store_logo_url = None

    return JsonResponse(
        {
            "ok": True,
            "profile_photo_url": profile_photo_url,
            "store_logo_url": store_logo_url,
        }
    )


@login_required
def my_account_noti_fragment(request):
    qs = Notification.objects.filter(user=request.user).order_by("-created_at")
    total = qs.count()
    unread = qs.filter(is_read=False).count()

    return render(request, "my_account/tabs/_noti_list.html", {
        "notifications": qs[:200],  # cap
        "noti_total": total,
        "noti_unread": unread,
    })


@login_required
def my_account_noti_mark_read(request, pk):
    if request.method != "POST":
        return JsonResponse({"ok": False}, status=405)

    n = get_object_or_404(Notification, pk=pk, user=request.user)
    if not n.is_read:
        n.is_read = True
        n.save(update_fields=["is_read"])

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"ok": True, "unread": unread})


@login_required
def my_account_noti_mark_all_read(request):
    if request.method != "POST":
        return JsonResponse({"ok": False}, status=405)

    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"ok": True, "unread": 0})


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