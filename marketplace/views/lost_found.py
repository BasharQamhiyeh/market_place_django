import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from marketplace.forms import ReportForm
from marketplace.models import City
from marketplace.models.lost_found import Report, ReportPhoto, ReportMatch


# ─────────────────────────────────────────────
# List
# ─────────────────────────────────────────────
def report_list(request):
    report_type = request.GET.get("type", "")        # lost | found | ""
    category    = request.GET.get("category", "")
    city_id     = request.GET.get("city", "")
    q           = request.GET.get("q", "").strip()

    qs = (
        Report.objects
        .filter(status=Report.STATUS_ACTIVE, is_deleted=False)
        .select_related("user", "city")
        .prefetch_related("photos")
        .order_by("-created_at")
    )

    if report_type in (Report.TYPE_LOST, Report.TYPE_FOUND):
        qs = qs.filter(type=report_type)
    if category:
        qs = qs.filter(category=category)
    if city_id:
        qs = qs.filter(city_id=city_id)
    if len(q) >= 2:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(area__icontains=q))

    paginator  = Paginator(qs, 16)
    page_obj   = paginator.get_page(request.GET.get("page", 1))
    has_more   = page_obj.has_next()
    total      = paginator.count
    visible    = page_obj.end_index() if total else 0

    cities = City.objects.all().order_by("name")

    ctx = {
        "page_obj":   page_obj,
        "reports":    page_obj.object_list,
        "cities":     cities,
        "has_more":   has_more,
        "total_count": total,
        "visible_count": visible,
        "categories": Report.CATEGORY_CHOICES,
        "filters": {
            "type":     report_type,
            "category": category,
            "city":     city_id,
            "q":        q,
        },
    }

    if request.headers.get("HX-Request"):
        html = render_to_string("partials/_report_results.html", ctx, request=request)
        return JsonResponse({"html": html, "total_count": total, "visible_count": visible, "has_more": has_more})

    return render(request, "lost_found_list.html", ctx)


# ─────────────────────────────────────────────
# Detail
# ─────────────────────────────────────────────
def report_detail(request, report_id):
    report = get_object_or_404(
        Report.objects.select_related("user", "city").prefetch_related("photos"),
        id=report_id,
        status=Report.STATUS_ACTIVE,
        is_deleted=False,
    )

    # session-based view count
    session_key = f"report_viewed_{report_id}"
    if not request.session.get(session_key):
        request.session[session_key] = True

    owner = report.user
    can_see_phone = report.show_phone and request.user.is_authenticated

    raw_phone = (owner.phone or "").strip()
    masked_phone = "07•• ••• •••"
    if raw_phone:
        masked_phone = raw_phone[:2] + "•• ••• •••"

    is_owner = request.user.is_authenticated and request.user.pk == owner.pk

    # Matches (only visible to owner)
    matches = []
    if is_owner:
        if report.type == Report.TYPE_LOST:
            matches = (
                ReportMatch.objects
                .filter(lost_report=report, found_report__status=Report.STATUS_ACTIVE, found_report__is_deleted=False)
                .select_related("found_report__user", "found_report__city")
                .prefetch_related("found_report__photos")
                .order_by("-score")[:10]
            )
        else:
            matches = (
                ReportMatch.objects
                .filter(found_report=report, lost_report__status=Report.STATUS_ACTIVE, lost_report__is_deleted=False)
                .select_related("lost_report__user", "lost_report__city")
                .prefetch_related("lost_report__photos")
                .order_by("-score")[:10]
            )

    return render(request, "lost_found_detail.html", {
        "report":         report,
        "is_owner":       is_owner,
        "can_see_phone":  can_see_phone,
        "phone_full":     raw_phone if can_see_phone else "",
        "phone_masked":   masked_phone,
        "matches":        matches,
    })


# ─────────────────────────────────────────────
# Create
# ─────────────────────────────────────────────
@login_required
def report_create(request):
    if request.method == "POST":
        token = request.POST.get("form_token")
        if not token or token != request.session.get("report_create_token"):
            from django.http import HttpResponseBadRequest
            return HttpResponseBadRequest("Invalid submission")
        del request.session["report_create_token"]

        form = ReportForm(request.POST)
        images = request.FILES.getlist("images")

        if form.is_valid():
            d = form.cleaned_data
            report = Report.objects.create(
                user=request.user,
                type=d["type"],
                title=d["title"],
                description=d.get("description") or "",
                category=d["category"],
                city=d.get("city"),
                area=d.get("area") or "",
                incident_date=d.get("incident_date"),
                show_phone=d.get("show_phone", True),
                contact_type=d.get("contact_type", Report.CONTACT_PHONE),
                status=Report.STATUS_PENDING,
            )

            for i, img in enumerate(images[:8]):
                ReportPhoto.objects.create(report=report, image=img, is_main=(i == 0))

            messages.success(request, "✅ تم إرسال بلاغك وهو الآن قيد المراجعة.")
            return redirect("my_reports")

        request.session["report_create_token"] = str(uuid.uuid4())
    else:
        form = ReportForm()
        request.session["report_create_token"] = str(uuid.uuid4())

    return render(request, "lost_found_create.html", {
        "form":       form,
        "form_token": request.session["report_create_token"],
        "cities":     City.objects.all().order_by("name"),
        "categories": Report.CATEGORY_CHOICES,
    })


# ─────────────────────────────────────────────
# Edit
# ─────────────────────────────────────────────
@login_required
def report_edit(request, report_id):
    report = get_object_or_404(
        Report.objects.filter(user=request.user, is_deleted=False),
        id=report_id,
    )

    if request.method == "POST":
        token = request.POST.get("form_token")
        if not token or token != request.session.get("report_edit_token"):
            from django.http import HttpResponseBadRequest
            return HttpResponseBadRequest("Invalid submission")
        del request.session["report_edit_token"]

        form = ReportForm(request.POST)
        new_images = request.FILES.getlist("images")

        if form.is_valid():
            d = form.cleaned_data
            report.type          = d["type"]
            report.title         = d["title"]
            report.description   = d.get("description") or ""
            report.category      = d["category"]
            report.city          = d.get("city")
            report.area          = d.get("area") or ""
            report.incident_date = d.get("incident_date")
            report.show_phone    = d.get("show_phone", True)
            report.contact_type  = d.get("contact_type", Report.CONTACT_PHONE)
            report.status        = Report.STATUS_PENDING  # needs re-moderation
            report.approved_by   = None
            report.approved_at   = None
            report.save()

            for i, img in enumerate(new_images[:8]):
                is_main = (i == 0) and not report.photos.filter(is_main=True).exists()
                ReportPhoto.objects.create(report=report, image=img, is_main=is_main)

            messages.success(request, "✅ تم تحديث البلاغ وهو الآن قيد المراجعة.")
            return redirect("my_reports")

        request.session["report_edit_token"] = str(uuid.uuid4())
    else:
        initial = {
            "type":          report.type,
            "title":         report.title,
            "description":   report.description,
            "category":      report.category,
            "city":          report.city,
            "area":          report.area,
            "incident_date": report.incident_date,
            "show_phone":    report.show_phone,
            "contact_type":  report.contact_type,
        }
        form = ReportForm(initial=initial)
        request.session["report_edit_token"] = str(uuid.uuid4())

    return render(request, "lost_found_edit.html", {
        "form":       form,
        "report":     report,
        "form_token": request.session["report_edit_token"],
        "cities":     City.objects.all().order_by("name"),
        "categories": Report.CATEGORY_CHOICES,
    })


# ─────────────────────────────────────────────
# Delete photo (AJAX)
# ─────────────────────────────────────────────
@login_required
@require_POST
def report_delete_photo(request, photo_id):
    photo = get_object_or_404(ReportPhoto, id=photo_id, report__user=request.user)
    photo.image.delete(save=False)
    photo.delete()
    return JsonResponse({"ok": True})


# ─────────────────────────────────────────────
# Soft-delete / cancel
# ─────────────────────────────────────────────
@login_required
@require_POST
def report_cancel(request, report_id):
    report = get_object_or_404(Report, id=report_id, user=request.user, is_deleted=False)
    report.is_deleted   = True
    report.deleted_at   = timezone.now()
    report.cancel_reason = request.POST.get("cancel_reason", "")
    report.save(update_fields=["is_deleted", "deleted_at", "cancel_reason"])
    messages.success(request, "تم حذف البلاغ.")
    return redirect("my_reports")


# ─────────────────────────────────────────────
# My Reports (in my_account tab or standalone)
# ─────────────────────────────────────────────
@login_required
def my_reports(request):
    reports = (
        Report.objects
        .filter(user=request.user, is_deleted=False)
        .select_related("city")
        .prefetch_related("photos")
        .order_by("-created_at")
    )
    return render(request, "my_reports.html", {"reports": reports})
