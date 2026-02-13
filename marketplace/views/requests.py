from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.db.models import Q
from django.utils import timezone, translation
from django.contrib import messages
from django.views.decorators.http import require_GET

from marketplace.forms import RequestForm
from marketplace.models import Request, Category, City, Listing, IssuesReport, RequestAttributeValue
from marketplace.services.notifications import notify, K_REQUEST, S_PENDING
from marketplace.utils.category_tree import build_category_tree, get_selected_category_path
from marketplace.views.helpers import _category_descendant_ids

import json
import uuid
from datetime import timedelta

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
            listing__is_deleted=False,
            listing__featured_until__gt=now,
        )
        .select_related("listing", "listing__category", "listing__city", "listing__user")
        .order_by("-listing__featured_until", "-listing__created_at")[:12]
    )

    base_qs = Request.objects.filter(
        listing__type="request",
        listing__is_approved=True,
        listing__is_active=True,
        listing__is_deleted=False
    ).select_related(
        "listing", "listing__user", "listing__category", "listing__city"
    ).order_by("-listing__featured_until")

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

    if condition:
        base_qs = base_qs.filter(condition_preference=condition)

    # seller type (store/individual)
    if seller_type:
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
        from marketplace.models import Banner  # adjust if your banner model is named differently
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


def request_detail(request, request_id):
    request_obj = get_object_or_404(Request, id=request_id)

    listing = request_obj.listing
    is_owner = request.user.is_authenticated and (listing.user_id == request.user.user_id)
    is_staff = request.user.is_authenticated and request.user.is_staff

    # ✅ Block public access to unapproved/inactive/deleted items
    if not (listing.is_approved and listing.is_active and not listing.is_deleted):
        if not (is_owner or is_staff):
            raise Http404()

    # ✅ Increment views (once per session per request)
    session_key = f"request_viewed_{request_id}"
    if not request.session.get(session_key):
        from django.db.models import F
        Listing.objects.filter(pk=listing.pk).update(views_count=F("views_count") + 1)
        request.session[session_key] = True
        listing.refresh_from_db(fields=["views_count"])

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
            listing__is_deleted=False
        )
        .exclude(id=request_obj.id)
        .order_by("-listing__published_at")[:4]
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

            notify(
                user=request.user,
                kind=K_REQUEST,
                status=S_PENDING,
                title="طلبك قيد المراجعة",
                body=f"طلبك \"{listing.title}\" قيد المراجعة حالياً.",
                listing=listing,
            )

            messages.success(request, "✅ Your request was submitted (pending review).")
            return redirect("my_account")

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


@login_required
@transaction.atomic
def request_edit(request, request_id):
    # ✅ Get Request through listing ownership
    req = get_object_or_404(
        Request.objects.select_related("listing", "listing__category", "listing__user"),
        id=request_id,
        listing__user=request.user,
    )

    listing = req.listing
    category = listing.category

    # =============================
    # Category tree (for display only; locked in edit)
    # =============================
    lang = translation.get_language()
    order_field = "name_ar" if lang == "ar" else "name_en"
    top_categories = Category.objects.filter(parent__isnull=True).order_by(order_field)

    category_tree = build_category_tree(top_categories, lang)
    category_tree_json = json.dumps(category_tree, ensure_ascii=False)

    selected_path = get_selected_category_path(category)
    selected_path_json = json.dumps(selected_path)

    # =============================
    # Form token (optional, like create)
    # =============================
    if "request_edit_form_token" not in request.session:
        request.session["request_edit_form_token"] = str(uuid.uuid4())

    # =============================
    # POST
    # =============================
    if request.method == "POST":
        token = request.POST.get("form_token")
        session_token = request.session.get("request_edit_form_token")
        if not token or token != session_token:
            return HttpResponseBadRequest("Duplicate or invalid submission")

        # consume token immediately to prevent double submit
        del request.session["request_edit_form_token"]

        # ✅ Security: prevent category tampering
        posted_category = request.POST.get("category")
        if posted_category and str(posted_category) != str(category.id):
            return HttpResponseForbidden("Category cannot be changed.")

        form = RequestForm(
            request.POST,
            category=category,
            instance=listing,                 # edits Listing
            initial={
                "budget": req.budget,
                "condition_preference": req.condition_preference,
            }
        )

        if form.is_valid():
            # 1) Save listing
            listing = form.save(commit=False)
            listing.category = category
            listing.is_approved = False
            listing.was_edited = True
            listing.show_phone = (request.POST.get("show_phone") == "on")
            listing.save()

            # 2) Save request-specific fields
            req.budget = form.cleaned_data.get("budget")
            req.condition_preference = form.cleaned_data.get("condition_preference")
            req.save()

            # 3) Rebuild attributes
            RequestAttributeValue.objects.filter(request=req).delete()

            for field_name, value in form.cleaned_data.items():
                if not field_name.startswith("attr_"):
                    continue
                if field_name.endswith("_other"):
                    continue

                try:
                    attr_id = int(field_name.split("_")[1])
                except Exception:
                    continue

                # Multi-select
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
                        final_value = str(value) if value is not None else ""

                if final_value:
                    RequestAttributeValue.objects.create(
                        request=req,
                        attribute_id=attr_id,
                        value=final_value,
                    )

            # refresh token for next edit attempt
            request.session["request_edit_form_token"] = str(uuid.uuid4())

            return redirect("my_account")

        # invalid form -> new token
        request.session["request_edit_form_token"] = str(uuid.uuid4())

    else:
        # GET form
        form = RequestForm(
            category=category,
            instance=listing,
            initial={
                "budget": req.budget,
                "condition_preference": req.condition_preference,
            }
        )

    return render(
        request,
        "request_edit.html",
        {
            "form": form,
            "req": req,
            "listing": listing,
            "selected_category": category,
            "category_tree_json": category_tree_json,
            "selected_category_path_json": selected_path_json,
            "form_token": request.session.get("request_edit_form_token"),
        },
    )

@require_GET
def request_detail_more_similar(request, request_id):
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 2))

    request_obj = get_object_or_404(Request, id=request_id)
    cat = getattr(request_obj.listing, "category", None)

    qs = (
        Request.objects
        .filter(
            listing__type="request",
            listing__is_active=True,
            listing__is_approved=True,
            listing__is_deleted=False
        )
        .exclude(id=request_obj.id)
        .select_related("listing__category", "listing__city", "listing__user")
        .order_by("-listing__created_at")
    )

    if cat:
        qs = qs.filter(listing__category=cat)

    chunk = list(qs[offset:offset + limit])

    html = render_to_string(
        "partials/_request_cards_only.html",
        {"latest_requests": chunk},  # ✅ FIX
        request=request
    )

    has_more = qs.count() > (offset + len(chunk))  # ✅ FIX
    return JsonResponse({"html": html, "has_more": has_more})