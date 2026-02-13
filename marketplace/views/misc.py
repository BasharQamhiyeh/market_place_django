import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.core.exceptions import ValidationError
from django.views.generic import TemplateView
from django.contrib import messages
from django.utils import translation

from pydantic import validate_email

from marketplace.models import ContactMessage, FAQCategory, PrivacyPolicyPage, Subscriber, Category, IssuesReport, \
    Listing, User, Store
from marketplace.validators import validate_no_links_or_html


def about(request):
    return render(request, "static_pages/about.html")


@require_http_methods(["GET", "POST"])
def contact_support(request):
    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        subject = (request.POST.get("subject") or "").strip()
        contact_method = (request.POST.get("contact_method") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()
        message_body = (request.POST.get("message") or "").strip()

        # minimal server-side validation
        if not full_name or not message_body or subject not in dict(ContactMessage.SUBJECT_CHOICES) or contact_method not in dict(ContactMessage.METHOD_CHOICES):
            return render(request, "static_pages/contact_support.html", {"submit_error": True})

        if contact_method == "phone":
            if not phone.startswith("07") or len(phone) != 10 or not phone.isdigit():
                return render(request, "static_pages/contact_support.html", {"submit_error": True})
            email = ""
        else:
            try:
                validate_email(email)
            except ValidationError:
                return render(request, "static_pages/contact_support.html", {"submit_error": True})
            phone = ""

        ContactMessage.objects.create(
            full_name=full_name,
            subject=subject,
            contact_method=contact_method,
            phone=phone or None,
            email=email or None,
            message=message_body,
        )

        # redirect to avoid resubmission on refresh
        return redirect("contact_support_done")

    return render(request, "static_pages/contact_support.html")


def contact_support_done(request):
    return render(request, "static_pages/contact_support.html", {"submitted": True})


class FAQView(TemplateView):
    template_name = "static_pages/faq.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        categories = (
            FAQCategory.objects
            .filter(is_active=True)
            .prefetch_related(
                # only active questions; ordered by model Meta ordering
                "questions"
            )
        )

        # Filter out inactive questions in python (simple and readable).
        # If you prefer pure DB filtering, I can give you a Prefetch(...) version too.
        cat_list = []
        for c in categories:
            qs = [q for q in c.questions.all() if q.is_active]
            if qs:
                c._active_questions = qs  # attach
                cat_list.append(c)

        ctx["faq_categories"] = cat_list
        return ctx


class WhyRuknView(TemplateView):
    template_name = "static_pages/why_rukn.html"


class PrivacyPolicyView(TemplateView):
    template_name = "static_pages/privacy_policy.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        page = (
            PrivacyPolicyPage.objects
            .prefetch_related("sections")
            .filter(is_active=True)
            .first()
        )

        if page:
            sections = [s for s in page.sections.all() if s.is_active]
        else:
            sections = []

        ctx["policy_page"] = page
        ctx["policy_sections"] = sections
        return ctx


def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            Subscriber.objects.get_or_create(email=email)
            messages.success(request, "✅ Thank you for subscribing!")
    return redirect('home')


@require_GET
def categories_browse(request):
    """
    صفحة تصفح الأقسام - Public page
    تعرض جميع الأقسام بشكل تفاعلي وجميل
    """

    lang = translation.get_language()

    top_categories = (
        Category.objects
        .filter(parent__isnull=True)
        .select_related("parent")
        .prefetch_related("subcategories__subcategories")
        .order_by("name_ar")
    )

    def title_of(cat):
        return cat.name_ar if lang == "ar" else cat.name_en

    def photo_of(cat):
        # uses your Category.photo_url property if you added it
        return getattr(cat, "photo_url", None) or None

    categories_data = []

    for top_cat in top_categories:
        subcats = top_cat.subcategories.all().order_by("name_ar")

        subs_list = []
        for sub in subcats:
            sub_sub_cats = sub.subcategories.all().order_by("name_ar")
            levels_list = [title_of(ssc) for ssc in sub_sub_cats] if sub_sub_cats.exists() else [title_of(sub)]

            subs_list.append({
                "id": sub.id,
                "title": title_of(sub),

                # ✅ NEW
                "photo": photo_of(sub),

                # optional legacy fallback
                "icon": sub.icon or "",
                "color": sub.color or "",
                "levels": levels_list,
            })

        categories_data.append({
            "id": top_cat.id,  # ✅ keep as int for simpler JS
            "title": title_of(top_cat),

            # ✅ NEW
            "photo": photo_of(top_cat),

            # optional legacy fallback
            "icon": top_cat.icon or "",
            "color": top_cat.color or "",
            "subs": subs_list,
        })

    context = {
        "categories_json": json.dumps(categories_data, ensure_ascii=False),
        "page_title": "تصفح الأقسام - ركن",
    }
    return render(request, "categories_browse.html", context)


@staff_member_required
def category_list(request):
    # Fetch all top-level categories (parent=None)
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')

    return render(request, 'category_list.html', {
        'categories': categories,
    })


def contact(request):
    return render(request, "contact_support.html")


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
        reported = get_object_or_404(User, user_id=target_id_int, is_active=True)
        if reported.user_id == request.user.user_id:
            return JsonResponse(
                {"ok": False, "message": "لا يمكنك الإبلاغ عن حسابك."},
                status=400
            )
        report.reported_user = reported
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