from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect, render
from django.contrib.admin.views.main import IS_POPUP_VAR
from django.utils.html import format_html
from django.db import models
from django.core.files.base import ContentFile
import tempfile, os, zipfile, openpyxl
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
import nested_admin, json
from django.utils import translation
from .forms import CityForm
from django import forms


from .models import (
    User, Category, Attribute, AttributeOption,
    Item, ItemAttributeValue, ItemPhoto, Notification,
    City, Favorite, IssuesReport, Message, Listing, Request, Store, StoreReview
)

# ======================================================
# ✅ USER ADMIN — read-only view with search
# ======================================================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "first_name", "last_name", "phone", "email", "last_login", "is_active")
    search_fields = ("first_name", "last_name", "username", "email", "phone")
    list_filter = ("is_active", "is_staff", "is_superuser")

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "is_verified", "is_active", "created_at")
    list_filter = ("is_verified", "is_active", "created_at")
    search_fields = ("name", "owner__phone", "owner__username")
    list_editable = ("is_verified", "is_active")


@admin.register(StoreReview)
class StoreReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "reviewer", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("store__name", "reviewer__phone", "reviewer__username")


class AttributeOptionInline(nested_admin.NestedTabularInline):
    model = AttributeOption
    extra = 1
    fields = ("value_en", "value_ar")
    verbose_name = "Option"
    verbose_name_plural = "Options"


class AttributeInline(nested_admin.NestedStackedInline):
    model = Attribute
    extra = 1
    fields = ("name_en", "name_ar", "input_type", "ui_type", "is_required")
    inlines = [AttributeOptionInline]
    verbose_name = "Attribute"
    verbose_name_plural = "Attributes"

    class Media:
        js = ("admin/attribute_options_toggle.js",)  # ✅ your static file path


class ItemPhotoInline(admin.TabularInline):
    model = ItemPhoto
    extra = 1
    fields = ("image", "is_main",)


@admin.register(Category)
class CategoryAdmin(nested_admin.NestedModelAdmin):
    change_list_template = "admin/categories_changelist.html"
    change_form_template = "admin/marketplace/category/change_form.html"
    list_display = ("name_en", "name_ar", "parent", "icon_display", "color_box")
    fields = (
        "name_en",
        "name_ar",
        "subtitle_en",
        "subtitle_ar",
        "child_label",
        "icon",
        "color",
        "description",
        "parent",
    )
    search_fields = ("name_en", "name_ar")
    list_filter = ("parent",)
    ordering = ("parent__id", "id")
    inlines = [AttributeInline]

    def _build_tree(self, qs, opts, parent=None):
        nodes = []
        children = qs.filter(parent=parent)
        for child in children:
            nodes.append({
                "id": child.id,
                "name": f"{child.name_en} / {child.name_ar}",
                "edit_url": reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[child.id]),
                "children": self._build_tree(qs, opts, child),
            })
        return nodes

    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request).select_related("parent")
        opts = self.model._meta
        tree = self._build_tree(qs, opts)
        extra_context = extra_context or {}
        extra_context["categories_json"] = json.dumps(tree, ensure_ascii=False)
        return super().changelist_view(request, extra_context=extra_context)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """
        Injects the same tree JSON into the add/edit form for visual context.
        """
        qs = self.get_queryset(request).select_related("parent")
        opts = self.model._meta
        tree = self._build_tree(qs, opts)
        extra_context = extra_context or {}
        extra_context["categories_json"] = json.dumps(tree, ensure_ascii=False)
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)

    def get_changeform_initial_data(self, request):
        """Pre-fill parent when ?parent=<id> is passed in the URL."""
        initial = super().get_changeform_initial_data(request)
        parent_id = request.GET.get("parent")
        if parent_id:
            initial["parent"] = parent_id
        return initial

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Hierarchical dropdown for parent selection."""
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "parent" and formfield is not None:
            categories = Category.objects.all().select_related("parent")
            lang = translation.get_language()

            def build_path(cat):
                name = cat.name_ar if lang == "ar" else cat.name_en
                path = [name]
                p = cat.parent
                while p:
                    pname = p.name_ar if lang == "ar" else p.name_en
                    path.insert(0, pname)
                    p = p.parent
                return " › ".join(path)

            choices = [(None, "---------")]
            for c in categories:
                choices.append((c.id, build_path(c)))

            formfield.choices = choices
        return formfield

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """
        Use a color picker for the 'color' field.
        """
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "color" and formfield is not None:
            formfield.widget = forms.TextInput(attrs={"type": "color"})
        return formfield

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "color" and formfield is not None:
            formfield.widget = forms.TextInput(attrs={"type": "color"})
        return formfield

    def icon_display(self, obj):
        if obj.icon:
            color = obj.color or "#ff6600"
            return format_html('<span style="font-size:22px; color:{};">{}</span>', color, obj.icon)
        return "—"
    icon_display.short_description = "Icon"

    def color_box(self, obj):
        if obj.color:
            return format_html(
                '<div style="width:25px; height:25px; background:{}; border-radius:4px; border:1px solid #ddd;"></div>',
                obj.color
            )
        return "—"
    color_box.short_description = "Color"

    class Media:
        js = (
            "admin/js/emoji_picker.js",
        )


# ======================================================
# ✅ ITEM ADMIN — cleaned, color-coded, review-based
# ======================================================
class ItemAttributeValueInline(admin.TabularInline):
    model = ItemAttributeValue
    extra = 0
    can_delete = False
    fields = ("attribute", "value")
    readonly_fields = ("attribute", "value")

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    change_form_template = "admin/marketplace/item/change_form.html"
    change_list_template = "admin/items_changelist.html"

    ordering = ("-listing__updated_at",)

    # ============================
    # LIST DISPLAY
    # ============================
    list_display = (
        "id",
        "listing_title",
        "listing_category",
        "price",
        "listing_user_username",
        "listing_user_first_name",
        "listing_user_last_name",
        "colored_status",
        "listing_approved_by",
        "listing_rejected_by",
        "listing_created_at",
        "condition",
        "listing_is_active",
        "external_id",
    )

    # ALL moderation fields now come from LISTING
    readonly_fields = (
        "listing_title",
        "listing_category",
        "listing_description",
        "listing_user",
        "listing_user_username",
        "listing_user_first_name",
        "listing_user_last_name",
        "listing_created_at",
        "listing_is_active",
        "colored_status",
        "photo_gallery",
        "listing_approved_by",
        "listing_rejected_by",
        "listing_approved_at",
        "listing_rejected_at",
        "external_id",
    )

    list_filter = (
        "listing__category",
        "listing__user",
        "listing__is_active",
        "listing__is_approved",
        "condition",
    )

    search_fields = (
        "listing__title",
        "listing__user__username",
        "listing__category__name_en",
        "listing__category__name_ar",
        "listing__user__first_name",
        "listing__user__last_name",
        "listing__user__email",
        "listing__user__phone",
        "external_id",
    )

    fields = (
        "listing_title",
        "listing_category",
        "price",
        "condition",
        "listing_description",
        "photo_gallery",
        "listing_user",
        "colored_status",
        "external_id",
        "listing_approved_by", "listing_approved_at",
        "listing_rejected_by", "listing_rejected_at",
    )

    # ============================
    # LISTING FIELDS (READ ONLY)
    # ============================
    inlines = [ItemPhotoInline, ItemAttributeValueInline]

    def listing_title(self, obj):
        return obj.listing.title

    listing_title.short_description = "Title"

    def listing_category(self, obj):
        return obj.listing.category

    listing_category.short_description = "Category"

    def listing_description(self, obj):
        return obj.listing.description

    listing_description.short_description = "Description"

    def listing_user(self, obj):
        return obj.listing.user

    listing_user.short_description = "User"

    def listing_user_username(self, obj):
        return obj.listing.user.username

    listing_user_username.short_description = "Username"

    def listing_user_first_name(self, obj):
        return obj.listing.user.first_name

    listing_user_first_name.short_description = "First Name"

    def listing_user_last_name(self, obj):
        return obj.listing.user.last_name

    listing_user_last_name.short_description = "Last Name"

    def listing_is_active(self, obj):
        return obj.listing.is_active

    listing_is_active.short_description = "Active?"

    def listing_created_at(self, obj):
        return obj.listing.created_at

    listing_created_at.short_description = "Created At"

    # ============================
    # Moderation fields (from LISTING)
    # ============================
    def listing_approved_by(self, obj):
        return obj.listing.approved_by

    listing_approved_by.short_description = "Approved By"

    def listing_rejected_by(self, obj):
        return obj.listing.rejected_by

    listing_rejected_by.short_description = "Rejected By"

    def listing_approved_at(self, obj):
        return obj.listing.approved_at

    listing_approved_at.short_description = "Approved At"

    def listing_rejected_at(self, obj):
        return obj.listing.rejected_at

    listing_rejected_at.short_description = "Rejected At"

    # -----------------------------
    # Custom URLs (Approve / Reject / Import)
    # -----------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:item_id>/approve/", self.admin_site.admin_view(self.approve_view), name="item_approve"),
            path("<int:item_id>/reject/", self.admin_site.admin_view(self.reject_view), name="item_reject"),
            path("import-excel/", self.admin_site.admin_view(self.import_excel_view), name="marketplace_item_import_excel"),
            # path("import-photos/", self.admin_site.admin_view(self.import_photos_view), name="marketplace_item_import_photos"),  # ✅ new
            path(
                "photo/<int:photo_id>/delete/",
                self.admin_site.admin_view(self.delete_photo_view),
                name="marketplace_item_delete_photo",
            ),
        ]
        return custom + urls

    # -----------------------------
    # Color-coded status display
    # -----------------------------
    def colored_status(self, obj):
        listing = obj.listing
        if listing.is_approved:
            color, text = "green", "Approved"
        elif not listing.is_active:
            color, text = "red", "Rejected"
        else:
            color, text = "orange", "Pending"
        return format_html(f'<b style="color:{color};">{text}</b>')
    colored_status.short_description = "Status"

    # -----------------------------
    # Approve view  ✅ records who + redirects to list
    # -----------------------------
    def approve_view(self, request, item_id):
        item = Item.objects.get(id=item_id)
        listing = item.listing  # ← IMPORTANT

        # Update LISTING moderation fields
        listing.is_approved = True
        listing.is_active = True
        listing.approved_by = request.user
        listing.rejected_by = None
        listing.approved_at = timezone.now()
        listing.rejected_at = None
        listing.save(update_fields=[
            "is_approved", "is_active",
            "approved_by", "rejected_by",
            "approved_at", "rejected_at"
        ])

        # Notification now references listing only
        Notification.objects.create(
            user=listing.user,
            listing=listing,
            title="✅ تمت الموافقة على إعلانك",
            body=f"إعلانك '{listing.title}' أصبح فعالاً الآن.",
        )

        self.message_user(request, "✅ Listing approved & user notified.", messages.SUCCESS)
        opts = self.model._meta
        return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"))

    # -----------------------------
    # Reject view  ✅ records who + redirects to list
    # -----------------------------
    def reject_view(self, request, item_id):
        item = Item.objects.get(id=item_id)
        listing = item.listing  # ← IMPORTANT

        if request.method == "POST":
            reason = request.POST.get("reason") or "غير مذكور"

            # Update LISTING moderation fields
            listing.is_approved = False
            listing.is_active = False
            listing.rejected_by = request.user
            listing.approved_by = None
            listing.rejected_at = timezone.now()
            listing.approved_at = None
            listing.save(update_fields=[
                "is_approved", "is_active",
                "rejected_by", "approved_by",
                "rejected_at", "approved_at"
            ])

            Notification.objects.create(
                user=listing.user,
                listing=listing,
                title="❌ تم رفض إعلانك",
                body=f"إعلانك '{listing.title}' تم رفضه. الأسباب: {reason}",
            )

            self.message_user(request, "❌ Listing rejected & user notified.", messages.ERROR)
            opts = self.model._meta
            return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"))

        # Render reject form
        opts = self.model._meta
        context = {
            "item": item,
            "listing": listing,
            "opts": opts,
            "original": item,
            "app_label": opts.app_label,
            IS_POPUP_VAR: False,
            "has_view_permission": True,
        }
        return render(request, "admin/marketplace/reject_reason.html", context)

    # -----------------------------
    # Photo gallery (read-only)
    # -----------------------------
    def photo_gallery(self, obj):
        photos = obj.photos.all()
        if not photos:
            return "No photos uploaded."

        html_parts = []
        for p in photos:
            delete_url = reverse("admin:marketplace_item_delete_photo", args=[p.id])
            html_parts.append(
                f"""
                <div style="display:inline-block;margin:6px;text-align:center;">
                  <img src="{p.image.url}"
                       style="width:160px;border-radius:8px;display:block;margin-bottom:4px;">
                  <a href="{delete_url}"
                     onclick="return confirm('Are you sure you want to delete this photo?');"
                     style="
                        display:inline-block;
                        padding:4px 10px;
                        background:#dc3545;
                        color:white;
                        border-radius:4px;
                        text-decoration:none;
                        font-size:12px;
                     ">
                    Delete
                  </a>
                </div>
                """
            )
        return format_html("".join(html_parts))
    photo_gallery.short_description = "Item Photos"

    def delete_photo_view(self, request, photo_id):
        photo = get_object_or_404(ItemPhoto, id=photo_id)
        item = photo.item

        # Optional: permission check
        if not self.has_change_permission(request, obj=item):
            raise PermissionDenied

        photo.delete()
        self.message_user(request, "🗑️ Photo deleted successfully.", level=messages.SUCCESS)

        listing = item.listing
        change_url = reverse("admin:marketplace_listing_change", args=[listing.pk])
        return redirect(change_url)

    # -----------------------------
    # Admin actions
    # -----------------------------
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"✅ {updated} items activated.")

    make_active.short_description = "Activate selected items"

    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"🚫 {updated} items deactivated.")

    make_inactive.short_description = "Deactivate selected items"

    # -----------------------------
    # Import Items (Excel + ZIP) — stores external_id ✅
    # -----------------------------
    def import_excel_view(self, request):
        """
        FINAL VERSION — EXACT OLD BEHAVIOR, adapted to Listing model.
        Fully working ZIP + URL photos.
        """

        import os, tempfile, zipfile, openpyxl, requests
        from django.core.files.base import ContentFile

        if request.method == "POST":
            excel_file = request.FILES.get("excel_file")
            zip_file = request.FILES.get("zip_file")

            if not excel_file and not zip_file:
                self.message_user(request, "⚠️ Upload Excel or ZIP.", level=messages.WARNING)
                return redirect("..")

            # ---------------------------
            # NORMALIZE external_id
            # ---------------------------
            def norm(v):
                if v is None:
                    return None
                try:
                    f = float(v)
                    if f.is_integer():
                        return str(int(f))
                    return str(v).strip()
                except:
                    return str(v).strip()

            excel_path = zip_path = photos_dir = None

            # ---------------------------
            # SAVE EXCEL
            # ---------------------------
            if excel_file:
                excel_path = tempfile.mktemp(suffix=".xlsx")
                with open(excel_path, "wb") as f:
                    for chunk in excel_file.chunks():
                        f.write(chunk)

            # ---------------------------
            # SAVE ZIP
            # ---------------------------
            if zip_file:
                if not zip_file.name.lower().endswith(".zip"):
                    self.message_user(request, "❌ ZIP only.", messages.ERROR)
                    return redirect("..")

                zip_path = tempfile.mktemp(suffix=".zip")
                photos_dir = tempfile.mkdtemp()

                with open(zip_path, "wb") as f:
                    for chunk in zip_file.chunks():
                        f.write(chunk)

                try:
                    with zipfile.ZipFile(zip_path, "r") as z:
                        z.extractall(photos_dir)
                except Exception as e:
                    self.message_user(request, f"❌ ZIP failed: {e}", messages.ERROR)
                    return redirect("..")

            created = updated = failed = added_photos = 0
            no_photo = []

            # ============================================================
            # 1️⃣ EXCEL IMPORT
            # ============================================================
            if excel_path:
                wb = openpyxl.load_workbook(excel_path)
                sheet = wb.active

                headers = [str(h.value).strip().lower() if h.value else "" for h in sheet[1]]

                def col(name):
                    for i, h in enumerate(headers):
                        if h == name:
                            return i
                    return None

                id_col = col("id")
                name_col = col("name")
                desc_col = col("description")
                price_col = col("price")
                cat_col = col("category")
                subcat_col = col("subcategory")
                city_col = col("city")
                img_col = col("image")

                for row in sheet.iter_rows(min_row=2, values_only=True):
                    try:
                        external_id = norm(row[id_col])
                        if not external_id:
                            continue

                        title = str(row[name_col]).strip()
                        desc = str(row[desc_col]).strip() if desc_col and row[desc_col] else ""
                        price = float(row[price_col]) if row[price_col] else 0.0
                        cat_name = str(row[cat_col]).strip()

                        subcat_name = (
                            str(row[subcat_col]).strip()
                            if subcat_col and row[subcat_col]
                            else None
                        )

                        city_name = (
                            str(row[city_col]).strip()
                            if city_col and row[city_col]
                            else None
                        )

                        # -----------------------------
                        # CATEGORY
                        # -----------------------------
                        cat, _ = Category.objects.get_or_create(
                            name_ar=cat_name,
                            defaults={"name_en": cat_name},
                        )

                        if subcat_name:
                            subcat, _ = Category.objects.get_or_create(
                                name_ar=subcat_name,
                                defaults={"name_en": subcat_name, "parent": cat},
                            )
                            if subcat.parent_id != cat.id:
                                subcat.parent = cat
                                subcat.save(update_fields=["parent"])
                            assigned_category = subcat
                        else:
                            assigned_category = cat

                        # -----------------------------
                        # CITY
                        # -----------------------------
                        if city_name:
                            city = City.objects.filter(
                                models.Q(name_ar__iexact=city_name) |
                                models.Q(name_en__iexact=city_name)
                            ).first() or City.objects.create(
                                name_ar=city_name, name_en=city_name
                            )
                        else:
                            city = None

                        # ======================================================
                        # FIND ITEM BY external_id
                        # ======================================================
                        item = Item.objects.filter(external_id=external_id).first()

                        if not item:
                            # CREATE LISTING FIRST
                            listing = Listing.objects.create(
                                type="item",
                                user=request.user,
                                title=title,
                                description=desc,
                                category=assigned_category,
                                city=city,
                                is_active=True,
                                is_approved=True,
                            )

                            item = Item.objects.create(
                                external_id=external_id,
                                listing=listing,
                                price=price,
                                condition="new",
                            )
                            created += 1

                        else:
                            # UPDATE EXISTING ITEM
                            item.price = price
                            item.condition = "new"
                            item.save(update_fields=["price", "condition"])
                            updated += 1

                            # ensure listing exists
                            listing = item.listing
                            listing.title = title
                            listing.description = desc
                            listing.category = assigned_category
                            listing.city = city
                            listing.user = request.user
                            listing.is_active = True
                            listing.is_approved = True
                            listing.save()

                        # ======================================================
                        # PHOTOS — EXACT OLD BEHAVIOR
                        # ======================================================
                        image_found = False
                        ext_lower = external_id.lower()

                        # ---- ZIP ----
                        if photos_dir:
                            for root, _, files in os.walk(photos_dir):
                                for fn in files:
                                    if ext_lower in fn.lower():
                                        try:
                                            fp = os.path.join(root, fn)
                                            with open(fp, "rb") as img:
                                                c = ContentFile(img.read())
                                                c.name = f"{external_id}_{fn}"
                                                ItemPhoto.objects.create(item=item, image=c)
                                            image_found = True
                                            added_photos += 1
                                        except:
                                            pass

                        # ---- URL ----
                        # 2️⃣ URL PHOTOS — also add ALL images
                        # ---- URL ----
                        # 2️⃣ URL PHOTOS — also add ALL images
                        if img_col is not None and row[img_col]:
                            urls = [u.strip() for u in str(row[img_col]).split(",") if u.strip()]

                            for url in urls:
                                try:
                                    r = requests.get(url, timeout=10)
                                    if r.status_code == 200:
                                        base = os.path.basename(url.split("?")[0]) or f"{external_id}.jpg"
                                        unique_name = f"{external_id}_{base}"

                                        c = ContentFile(r.content)
                                        c.name = unique_name

                                        ItemPhoto.objects.create(item=item, image=c)
                                        image_found = True
                                        added_photos += 1
                                except Exception as e:
                                    print("URL DOWNLOAD ERROR:", url, e)
                                    pass

                        if not image_found:
                            no_photo.append(external_id)

                    except Exception as e:
                        print("ERROR ROW:", row, e)
                        failed += 1

                wb.close()

            # ============================================================
            # 2️⃣ ZIP ONLY — ADD PHOTOS ONLY
            # ============================================================
            elif zip_file and not excel_file:
                existing = {
                    norm(i.external_id): i
                    for i in Item.objects.exclude(external_id__isnull=True)
                    .exclude(external_id__exact="")
                }

                for root, _, files in os.walk(photos_dir):
                    for fn in files:
                        low = fn.lower()
                        for ext_id, item in existing.items():
                            if ext_id.lower() in low:
                                try:
                                    fp = os.path.join(root, fn)
                                    with open(fp, "rb") as img:
                                        c = ContentFile(img.read())
                                        c.name = fn
                                        ItemPhoto.objects.create(item=item, image=c)
                                    added_photos += 1
                                except:
                                    failed += 1

            # -----------------------
            # Cleanup
            # -----------------------
            for p in [excel_path, zip_path]:
                if p and os.path.exists(p):
                    os.remove(p)

            msg = f"✅ Done. {created} created, {updated} updated, {failed} failed."
            if added_photos:
                msg += f" {added_photos} photos added."
            if no_photo:
                msg += f" ⚠️ {len(no_photo)} items no photos."

            self.message_user(request, msg, level=messages.SUCCESS)
            return redirect("../")

        # GET
        return render(
            request,
            "admin/import_excel.html",
            {"title": "Import Items (Excel & ZIP)"},
        )


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    change_form_template = "admin/marketplace/request/change_form.html"
    ordering = ("-listing__updated_at",)

    # ============================
    # LIST DISPLAY
    # ============================
    list_display = (
        "id",
        "listing_title",
        "listing_category",
        "budget",
        "condition_preference",
        "listing_user_username",
        "colored_status",
        "listing_created_at",
        "listing_is_active",
    )

    readonly_fields = (
        "listing_title",
        "listing_category",
        "listing_description",
        "listing_user",
        "listing_user_username",
        "listing_user_first_name",
        "listing_user_last_name",
        "listing_created_at",
        "listing_is_active",
        "colored_status",
        "listing_approved_by",
        "listing_rejected_by",
        "listing_approved_at",
        "listing_rejected_at",
    )

    list_filter = (
        "listing__category",
        "listing__user",
        "listing__is_active",
        "listing__is_approved",
        "condition_preference",
    )

    search_fields = (
        "listing__title",
        "listing__user__username",
        "listing__user__first_name",
        "listing__user__last_name",
        "listing__category__name_ar",
        "listing__category__name_en",
        "listing__user__phone",
    )

    fields = (
        "listing_title",
        "listing_category",
        "budget",
        "condition_preference",
        "show_phone",
        "listing_description",
        "listing_user",
        "colored_status",
        "listing_approved_by", "listing_approved_at",
        "listing_rejected_by", "listing_rejected_at",
    )

    # ============================
    # LISTING WRAPPER FIELDS
    # ============================

    def listing_title(self, obj):
        return obj.listing.title
    listing_title.short_description = "Title"

    def listing_category(self, obj):
        return obj.listing.category
    listing_category.short_description = "Category"

    def listing_description(self, obj):
        return obj.listing.description
    listing_description.short_description = "Description"

    def listing_user(self, obj):
        return obj.listing.user
    listing_user.short_description = "User"

    def listing_user_username(self, obj):
        return obj.listing.user.username
    listing_user_username.short_description = "Username"

    def listing_user_first_name(self, obj):
        return obj.listing.user.first_name
    listing_user_first_name.short_description = "First Name"

    def listing_user_last_name(self, obj):
        return obj.listing.user.last_name
    listing_user_last_name.short_description = "Last Name"

    def listing_is_active(self, obj):
        return obj.listing.is_active
    listing_is_active.short_description = "Active?"

    def listing_created_at(self, obj):
        return obj.listing.created_at
    listing_created_at.short_description = "Created At"

    # ============================
    # MODERATION
    # ============================

    def listing_approved_by(self, obj):
        return obj.listing.approved_by
    listing_approved_by.short_description = "Approved By"

    def listing_rejected_by(self, obj):
        return obj.listing.rejected_by
    listing_rejected_by.short_description = "Rejected By"

    def listing_approved_at(self, obj):
        return obj.listing.approved_at
    listing_approved_at.short_description = "Approved At"

    def listing_rejected_at(self, obj):
        return obj.listing.rejected_at
    listing_rejected_at.short_description = "Rejected At"

    # ============================
    # STATUS
    # ============================
    def colored_status(self, obj):
        listing = obj.listing
        if listing.is_approved:
            color, text = "green", "Approved"
        elif not listing.is_active:
            color, text = "red", "Rejected"
        else:
            color, text = "orange", "Pending"

        return format_html(f'<b style="color:{color};">{text}</b>')
    colored_status.short_description = "Status"

    # ============================
    # APPROVE / REJECT URLS
    # ============================
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:request_id>/approve/", self.admin_site.admin_view(self.approve_view), name="request_approve"),
            path("<int:request_id>/reject/", self.admin_site.admin_view(self.reject_view), name="request_reject"),
        ]
        return custom + urls

    # Approve request
    def approve_view(self, request, request_id):
        req = Request.objects.get(id=request_id)
        listing = req.listing

        listing.is_approved = True
        listing.is_active = True
        listing.approved_by = request.user
        listing.rejected_by = None
        listing.rejected_at = None
        listing.approved_at = timezone.now()
        listing.save()

        Notification.objects.create(
            user=listing.user,
            listing=listing,
            title="✅ تم قبول طلب الشراء",
            body=f"طلبك '{listing.title}' تم قبوله.",
        )

        self.message_user(request, "تم قبول الطلب", messages.SUCCESS)

        opts = self.model._meta
        return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"))

    # Reject request
    def reject_view(self, request, request_id):
        req = Request.objects.get(id=request_id)
        listing = req.listing

        if request.method == "POST":
            reason = request.POST.get("reason", "غير مذكور")

            listing.is_approved = False
            listing.is_active = False
            listing.rejected_by = request.user
            listing.approved_by = None
            listing.rejected_at = timezone.now()
            listing.approved_at = None
            listing.save()

            Notification.objects.create(
                user=listing.user,
                listing=listing,
                title="❌ تم رفض طلب الشراء",
                body=f"تم رفض طلبك. السبب: {reason}",
            )

            self.message_user(request, "تم رفض الطلب", messages.ERROR)

            opts = self.model._meta
            return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"))

        # Render reject reason form
        opts = self.model._meta
        context = {
            "request_obj": req,
            "listing": listing,
            "opts": opts,
            "original": req,
            "app_label": opts.app_label,
            IS_POPUP_VAR: False,
            "has_view_permission": True,
        }
        return render(request, "admin/marketplace/reject_reason.html", context)



# # ======================================================
# # ✅ OTHER ADMINS
# # ======================================================
# @admin.register(ItemAttributeValue)
# class ItemAttributeValueAdmin(admin.ModelAdmin):
#     list_display = ("id", "item", "attribute", "value")
#     search_fields = ("value",)
#     list_filter = ("attribute",)

#
# @admin.register(ItemPhoto)
# class ItemPhotoAdmin(admin.ModelAdmin):
#     list_display = ("id", "item", "image", "created_at")
#     list_filter = ("item",)
#     search_fields = ("item__title",)


# @admin.register(Notification)
# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "title", "is_read", "created_at")
#     list_filter = ("is_read",)
#     search_fields = ("title", "body", "user__username")


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name_ar", "name_en", "is_active")
    ordering = ("name_ar",)
    search_fields = ("name_ar", "name_en")
    change_list_template = "admin/cities_list_and_form.html"

    def changelist_view(self, request, extra_context=None):
        """Show list and add form on same page."""
        extra_context = extra_context or {}
        form = CityForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            form.save()
            return redirect(request.path)
        extra_context["form"] = form
        return super().changelist_view(request, extra_context=extra_context)





from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation_info",
        "sender_info",
        "receiver_info",
        "short_body",
        "is_read",
        "created_at",
    )
    readonly_fields = (
        "conversation_display",
        "sender_display",
        "receiver_display",
        "body",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "created_at")
    search_fields = (
        "body",
        "sender__username", "sender__first_name", "sender__last_name", "sender__phone",
        "conversation__buyer__username", "conversation__buyer__first_name",
        "conversation__buyer__last_name", "conversation__buyer__phone",
        "conversation__seller__username", "conversation__seller__first_name",
        "conversation__seller__last_name", "conversation__seller__phone",
    )
    ordering = ("-created_at",)
    list_select_related = ("sender", "conversation")

    # Hide add/edit/delete permissions
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # allow viewing but disable form fields editing
        if obj:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        return False


    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        extra_context['show_delete'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

    # Show read-only details instead of form fields
    def get_fields(self, request, obj=None):
        return (
            "conversation_display",
            "sender_display",
            "receiver_display",
            "body",
            "is_read",
            "created_at",
        )

    # ========= List page helpers =========
    def short_body(self, obj):
        return (obj.body[:60] + "...") if len(obj.body) > 60 else obj.body
    short_body.short_description = "Message"

    def conversation_info(self, obj):
        return str(obj.conversation)
    conversation_info.short_description = "Conversation"

    def sender_info(self, obj):
        sender = obj.sender
        return f"{sender.username} ({sender.first_name} {sender.last_name})"
    sender_info.short_description = "Sender"

    def receiver_info(self, obj):
        conv = obj.conversation
        if obj.sender == conv.buyer:
            receiver = conv.seller
        elif obj.sender == conv.seller:
            receiver = conv.buyer
        else:
            return "-"
        return f"{receiver.username} ({receiver.first_name} {receiver.last_name})"
    receiver_info.short_description = "Receiver"

    # ========= Read-only detail view =========
    def conversation_display(self, obj):
        return str(obj.conversation)
    conversation_display.short_description = "Conversation"

    def sender_display(self, obj):
        sender = obj.sender
        url = reverse("admin:marketplace_user_change", args=[sender.user_id])
        return format_html(
            '<a href="{}"><b>{}</b></a><br>{} {} — {}',
            url,
            sender.username,
            sender.first_name,
            sender.last_name,
            sender.phone or "No phone",
        )
    sender_display.short_description = "Sender"

    def receiver_display(self, obj):
        conv = obj.conversation
        if obj.sender == conv.buyer:
            receiver = conv.seller
        elif obj.sender == conv.seller:
            receiver = conv.buyer
        else:
            return "-"
        url = reverse("admin:marketplace_user_change", args=[receiver.user_id])
        return format_html(
            '<a href="{}"><b>{}</b></a><br>{} {} — {}',
            url,
            receiver.username,
            receiver.first_name,
            receiver.last_name,
            receiver.phone or "No phone",
        )
    receiver_display.short_description = "Receiver"


# @admin.register(Favorite)
# class FavoriteAdmin(admin.ModelAdmin):
#     list_display = ("user", "item", "created_at")
#     list_filter = ("created_at",)
#     search_fields = ("user__username", "item__title")



@admin.register(IssuesReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "target_kind",
        "listing_type",
        "status",
        "created_at",
    )

    list_filter = (
        "target_kind",
        "listing_type",
        "status",
        "created_at",
    )

    search_fields = (
        "message",
        "user__first_name",
        "user__phone",
    )

    ordering = ("-created_at",)



# Reorder models in the app list
def custom_get_app_list(self, request):
    """
    Reorder the models in the 'marketplace' app section on the admin index.
    """
    # Get the default list from the AdminSite itself
    app_list = admin.site._build_app_dict(request).values()

    # Convert dict_values to list
    app_list = sorted(app_list, key=lambda x: x["name"].lower())

    for app in app_list:
        if app["app_label"] == "marketplace":
            desired_order = ["Item", "Category", "City", "User", "IssueReport"]
            app["models"].sort(
                key=lambda m: desired_order.index(m["object_name"])
                if m["object_name"] in desired_order else 999
            )
    return app_list

# ✅ Patch the method onto the current admin site instance
admin.site.get_app_list = custom_get_app_list.__get__(admin.site, admin.AdminSite)

# ======================================================
# ✅ Admin Branding
# ======================================================
admin.site.site_header = "Rokon Administration"
admin.site.index_title = "Control Panel"
admin.site.site_title = "Rokon Admin"
