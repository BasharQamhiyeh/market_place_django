import base64
import json
import uuid

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from marketplace.models import City
from marketplace.models.lost_found import Report, ReportPhoto


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _report_to_js(report, is_own=False):
    """Serialize a Report to the JS-compatible dict the SPA expects."""
    photos = list(report.photos.order_by('id'))
    main_idx = next((i for i, p in enumerate(photos) if p.is_main), 0)

    user = report.user
    owner_name = (
        user.username
        or f"{user.first_name} {user.last_name}".strip()
        or "مستخدم"
    )

    avatar = ""
    if user.profile_photo:
        try:
            avatar = user.profile_photo.url
        except Exception:
            pass

    cat_map = dict(Report.CATEGORY_CHOICES)
    cat_label = cat_map.get(report.category, "أخرى")

    return {
        "id": report.id,
        "type": "مفقود" if report.type == Report.TYPE_LOST else "موجود",
        "title": report.title,
        "desc": report.description,
        "cat": cat_label,
        "city": report.city.name if report.city else "",
        "area": report.area or "",
        "date": report.created_at.strftime("%d/%m/%Y"),
        "createdAt": int(report.created_at.timestamp() * 1000),
        "owner": owner_name,
        "avatar": avatar,
        "showPhone": report.show_phone,
        "phone": (user.phone or None) if report.show_phone else None,
        "images": [p.image.url for p in photos],
        "mainImageIndex": main_idx,
        "isOwn": is_own,
        "status": report.status,
    }


def _save_images(report, images_list, main_image_index, existing_photos=None):
    """Create/keep photos for a report. Deletes removed existing ones on update."""
    existing_url_map = {}
    if existing_photos is not None:
        existing_url_map = {p.image.url: p for p in existing_photos}

    kept_ids = set()
    for i, img_data in enumerate(images_list[:8]):
        is_main = (i == main_image_index)
        if img_data.startswith('data:image'):
            try:
                header, b64data = img_data.split(';base64,', 1)
                ext = header.split('/')[-1].replace('jpeg', 'jpg').replace('jpg', 'jpg')
                img_file = ContentFile(
                    base64.b64decode(b64data),
                    name=f"{uuid.uuid4()}.{ext}"
                )
                photo = ReportPhoto.objects.create(report=report, image=img_file, is_main=is_main)
                kept_ids.add(photo.id)
            except Exception:
                pass
        elif img_data:
            # Existing URL — find the matching photo record
            photo = existing_url_map.get(img_data)
            if photo:
                photo.is_main = is_main
                photo.save(update_fields=['is_main'])
                kept_ids.add(photo.id)

    # Delete photos not in the submitted list (edit only)
    if existing_photos is not None:
        for photo in existing_photos:
            if photo.id not in kept_ids:
                try:
                    photo.image.delete(save=False)
                except Exception:
                    pass
                photo.delete()


# ─────────────────────────────────────────────
# Main page
# ─────────────────────────────────────────────
def lost_found_page(request):
    # Active public reports
    public_qs = (
        Report.objects
        .filter(status=Report.STATUS_ACTIVE, is_deleted=False)
        .select_related("user", "city")
        .prefetch_related("photos")
        .order_by("-created_at")[:300]
    )

    my_ids_set = set()
    my_reports_qs = []
    if request.user.is_authenticated:
        my_reports_qs = list(
            Report.objects
            .filter(user=request.user, is_deleted=False)
            .select_related("user", "city")
            .prefetch_related("photos")
            .order_by("-created_at")
        )
        my_ids_set = {r.id for r in my_reports_qs}

    # Build combined ads map (deduplicated by id)
    ads_map = {}
    for r in public_qs:
        ads_map[r.id] = _report_to_js(r, is_own=(r.id in my_ids_set))
    for r in my_reports_qs:
        ads_map[r.id] = _report_to_js(r, is_own=True)

    user_phone = ""
    if request.user.is_authenticated:
        user_phone = (request.user.phone or "").strip()

    initial_data = {
        "reports": list(ads_map.values()),
        "myIds": list(my_ids_set),
        "userPhone": user_phone,
        "isAuthenticated": request.user.is_authenticated,
        "csrfToken": get_token(request),
        "loginUrl": "/login/",
    }

    cities = City.objects.all().order_by("name")

    return render(request, "lost_found.html", {
        "initial_data_json": json.dumps(initial_data, cls=DjangoJSONEncoder, ensure_ascii=False),
        "cities": cities,
        "categories": Report.CATEGORY_CHOICES,
    })


# ─────────────────────────────────────────────
# AJAX: Create or Update
# ─────────────────────────────────────────────
@login_required
@require_POST
def ajax_report_save(request):
    report_id    = request.POST.get("report_id", "").strip()
    report_type  = request.POST.get("type", "").strip()   # 'lost' | 'found'
    cat_label    = request.POST.get("cat", "").strip()    # Arabic label
    title        = request.POST.get("title", "").strip()
    desc         = request.POST.get("desc", "").strip()
    city_name    = request.POST.get("city", "").strip()
    area         = request.POST.get("area", "").strip()
    show_phone   = request.POST.get("show_phone", "false") == "true"
    images_json  = request.POST.get("images_json", "[]")
    main_idx_str = request.POST.get("main_image_index", "0")

    # Validate required fields
    if not title:
        return JsonResponse({"ok": False, "error": "العنوان مطلوب"})
    if not cat_label:
        return JsonResponse({"ok": False, "error": "التصنيف مطلوب"})
    if not city_name:
        return JsonResponse({"ok": False, "error": "المدينة مطلوبة"})
    if report_type not in (Report.TYPE_LOST, Report.TYPE_FOUND):
        return JsonResponse({"ok": False, "error": "نوع البلاغ غير صحيح"})

    # Map Arabic label → DB key
    cat_key = next(
        (k for k, v in Report.CATEGORY_CHOICES if v == cat_label),
        Report.CAT_OTHER
    )

    # Lookup city
    city = City.objects.filter(name=city_name).first()

    # Parse images
    try:
        images_list = json.loads(images_json)
    except Exception:
        images_list = []

    try:
        main_idx = int(main_idx_str)
    except ValueError:
        main_idx = 0

    if report_id:
        # ── UPDATE ──────────────────────────────
        try:
            report = Report.objects.get(id=report_id, user=request.user, is_deleted=False)
        except Report.DoesNotExist:
            return JsonResponse({"ok": False, "error": "البلاغ غير موجود"})

        report.type        = report_type
        report.title       = title
        report.description = desc
        report.category    = cat_key
        report.city        = city
        report.area        = area
        report.show_phone  = show_phone
        report.status      = Report.STATUS_PENDING
        report.approved_by = None
        report.approved_at = None
        report.save()

        existing_photos = list(report.photos.all())
        _save_images(report, images_list, main_idx, existing_photos=existing_photos)
    else:
        # ── CREATE ──────────────────────────────
        report = Report.objects.create(
            user        = request.user,
            type        = report_type,
            title       = title,
            description = desc,
            category    = cat_key,
            city        = city,
            area        = area,
            show_phone  = show_phone,
            status      = Report.STATUS_PENDING,
        )
        _save_images(report, images_list, main_idx)

    report.refresh_from_db()
    report.photos.prefetch_related  # force fresh prefetch
    return JsonResponse({
        "ok": True,
        "report": _report_to_js(
            Report.objects.prefetch_related("photos").select_related("user", "city").get(pk=report.pk),
            is_own=True
        )
    })


# ─────────────────────────────────────────────
# AJAX: Delete (soft)
# ─────────────────────────────────────────────
@login_required
@require_POST
def ajax_report_delete(request, report_id):
    try:
        report = Report.objects.get(id=report_id, user=request.user, is_deleted=False)
    except Report.DoesNotExist:
        return JsonResponse({"ok": False, "error": "البلاغ غير موجود"})

    report.is_deleted = True
    report.deleted_at = timezone.now()
    report.save(update_fields=["is_deleted", "deleted_at"])

    return JsonResponse({"ok": True})
