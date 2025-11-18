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
    City, Favorite, IssueReport, Message
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


class AttributeOptionInline(nested_admin.NestedTabularInline):
    model = AttributeOption
    extra = 1
    fields = ("value_en", "value_ar")
    verbose_name = "Option"
    verbose_name_plural = "Options"


class AttributeInline(nested_admin.NestedStackedInline):
    model = Attribute
    extra = 1
    fields = ("name_en", "name_ar", "input_type", "is_required")
    inlines = [AttributeOptionInline]
    verbose_name = "Attribute"
    verbose_name_plural = "Attributes"

    class Media:
        js = ("admin/attribute_options_toggle.js",)  # ✅ your static file path


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
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    change_form_template = "admin/marketplace/item/change_form.html"
    change_list_template = "admin/items_changelist.html"

    # inlines = [ItemPhotoInline]

    ordering = ("-updated_at",)

    list_display = (
        "id", "title", "category", "price",
        "get_username", "get_first_name", "get_last_name",
        "colored_status", "approved_by", "rejected_by",
        "created_at", "condition", "is_active", "external_id"
    )
    readonly_fields = ("colored_status", "photo_gallery", "approved_by", "rejected_by", "approved_at", "rejected_at", "external_id")
    list_filter = ("category", "user", "is_active", "is_approved", "condition")
    search_fields = (
        "title",
        "user__username",
        "category__name_en",
        "category__name_ar",
        "user__first_name", "user__last_name", "user__email", "user__phone",
        "external_id",   # ✅ searchable
    )
    actions = ["make_active", "make_inactive"]

    fields = (
        "title",
        "category",
        "price",
        "condition",
        "description",
        "photo_gallery",
        "user",
        "colored_status",
        "external_id",      # ✅ visible (read-only) for reference
        "approved_by", "approved_at",
        "rejected_by", "rejected_at",
    )

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = "Username"

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.short_description = "First Name"

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.short_description = "Last Name"

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
        if obj.is_approved:
            color, text = "green", "Approved"
        elif not obj.is_active:
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
        item.is_approved = True
        item.is_active = True
        item.approved_by = request.user
        item.rejected_by = None
        item.approved_at = timezone.now()
        item.rejected_at = None
        item.save(update_fields=[
            "is_approved", "is_active", "approved_by", "rejected_by", "approved_at", "rejected_at"
        ])

        Notification.objects.create(
            user=item.user,
            title="✅ تمت الموافقة على إعلانك",
            body=f"إعلانك '{item.title}' أصبح فعالاً الآن.",
            item=item,
        )

        self.message_user(request, "✅ Item approved & user notified.", messages.SUCCESS)
        opts = self.model._meta
        return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"))

    # -----------------------------
    # Reject view  ✅ records who + redirects to list
    # -----------------------------
    def reject_view(self, request, item_id):
        item = Item.objects.get(id=item_id)
        if request.method == "POST":
            reason = request.POST.get("reason") or "غير مذكور"
            item.is_approved = False
            item.is_active = False
            item.rejected_by = request.user
            item.approved_by = None
            item.rejected_at = timezone.now()
            item.approved_at = None
            item.save(update_fields=[
                "is_approved", "is_active", "rejected_by", "approved_by", "rejected_at", "approved_at"
            ])

            Notification.objects.create(
                user=item.user,
                title="❌ تم رفض إعلانك",
                body=f"إعلانك '{item.title}' تم رفضه. الأسباب: {reason}",
                item=item,
            )

            self.message_user(request, "❌ Item rejected & user notified.", messages.ERROR)
            opts = self.model._meta
            return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"))

        opts = self.model._meta
        context = {
            "item": item,
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

        opts = self.model._meta
        change_url = reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[item.pk])
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
        Import items from Excel (.xlsx) and/or photos from ZIP.
        You can upload:
          - Excel only  → create/update items (no photos)
          - ZIP only    → add photos to existing items (matched by external_id)
          - Both files  → full import (items + photos)
        """
        if request.method == "POST":
            excel_file = request.FILES.get("excel_file")
            zip_file = request.FILES.get("zip_file")

            if not excel_file and not zip_file:
                self.message_user(request, "⚠️ Please upload at least one file (Excel or ZIP).", level=messages.WARNING)
                return redirect("..")

            # helper to normalize external_id values from Excel / DB
            def normalize_external_id(raw):
                if raw is None:
                    return None
                # if it's already numeric (int/float), drop .0 etc.
                if isinstance(raw, (int, float)):
                    try:
                        return str(int(raw))
                    except Exception:
                        return str(raw).strip()
                s = str(raw).strip()
                # try to convert strings like "123.0" -> "123"
                try:
                    f = float(s)
                    if f.is_integer():
                        return str(int(f))
                except Exception:
                    pass
                return s or None

            # Temporary paths
            excel_path, zip_path, photos_dir = None, None, None

            # --- Handle Excel ---------------------------------
            if excel_file:
                excel_path = tempfile.mktemp(suffix=".xlsx")
                with open(excel_path, "wb+") as f:
                    for chunk in excel_file.chunks():
                        f.write(chunk)

            # --- Handle ZIP -----------------------------------
            if zip_file:
                if not zip_file.name.lower().endswith(".zip"):
                    self.message_user(request, "❌ Only .zip files are supported.", level=messages.ERROR)
                    return redirect("..")
                zip_path = tempfile.mktemp(suffix=".zip")
                photos_dir = tempfile.mkdtemp()
                with open(zip_path, "wb+") as f:
                    for chunk in zip_file.chunks():
                        f.write(chunk)

                try:
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(photos_dir)
                except Exception as e:
                    self.message_user(request, f"❌ Failed to extract ZIP: {e}", level=messages.ERROR)
                    return redirect("..")

            created, failed, updated, no_photo, added_photos = 0, 0, 0, [], 0

            import requests

            # --- 1️⃣ Excel import (create/update items) -----------
            if excel_path:
                wb = openpyxl.load_workbook(excel_path)
                sheet = wb.active
                headers = [str(c.value).strip().lower() if c.value else "" for c in sheet[1]]

                def col(name):
                    for i, h in enumerate(headers):
                        if h == name.lower():
                            return i
                    return None

                id_col = col("id")
                name_col = col("name")
                desc_col = col("description")
                price_col = col("price")
                category_col = col("category")
                subcategory_col = col("subcategory")
                city_col = col("city")
                image_col = col("image")

                required = [id_col, name_col, price_col, category_col]
                if any(c is None for c in required):
                    missing = [n for n, c in zip(["id", "name", "price", "category"], required) if c is None]
                    self.message_user(request, f"❌ Missing columns: {', '.join(missing)}", level=messages.ERROR)
                    return redirect("..")

                for row in sheet.iter_rows(min_row=2, values_only=True):
                    try:
                        # ✅ normalize external_id from Excel
                        external_id = normalize_external_id(row[id_col]) if row[id_col] is not None else None
                        title = str(row[name_col]).strip() if row[name_col] else None
                        desc = str(row[desc_col]).strip() if desc_col and row[desc_col] else ""
                        price = float(row[price_col]) if row[price_col] is not None else None
                        category_name = str(row[category_col]).strip() if row[category_col] else None
                        subcategory_name = (
                            str(row[subcategory_col]).strip() if subcategory_col and row[subcategory_col] else None
                        )
                        city_name = str(row[city_col]).strip() if city_col and row[city_col] else None

                        if not external_id or not title or price is None or not category_name:
                            continue

                        # --- Category/subcategory
                        category, _ = Category.objects.get_or_create(
                            name_ar=category_name,
                            defaults={"name_en": category_name},
                        )
                        if subcategory_name:
                            subcategory, _ = Category.objects.get_or_create(
                                name_ar=subcategory_name,
                                defaults={"name_en": subcategory_name, "parent": category},
                            )
                            if subcategory.parent_id != category.id:
                                subcategory.parent = category
                                subcategory.save(update_fields=["parent"])
                            assigned_category = subcategory
                        else:
                            assigned_category = category

                        # --- City
                        city = None
                        if city_name:
                            city = City.objects.filter(
                                models.Q(name_ar__iexact=city_name) | models.Q(name_en__iexact=city_name)
                            ).first() or City.objects.create(name_ar=city_name, name_en=city_name)

                        image_found = False

                        # --- Create or update item
                        item, created_item = Item.objects.update_or_create(
                            external_id=external_id,
                            defaults={
                                "title": title,
                                "description": desc,
                                "price": price,
                                "category": assigned_category,
                                "city": city,
                                "user": request.user,
                                "is_active": True,
                                "condition": "new",
                            },
                        )
                        if created_item:
                            created += 1
                        else:
                            updated += 1

                        # --- Attach images (ZIP or URL)
                        if photos_dir:
                            # we already know the normalized external_id, so reuse it
                            for root, _, files in os.walk(photos_dir):
                                for filename in files:
                                    if external_id.lower() in filename.lower():
                                        try:
                                            with open(os.path.join(root, filename), "rb") as img_file:
                                                content = ContentFile(img_file.read())
                                                content.name = filename
                                                ItemPhoto.objects.create(item=item, image=content)
                                                image_found = True
                                                added_photos += 1
                                        except Exception as e:
                                            print(f"[WARN] Could not save {filename}: {e}")

                        if image_col is not None and row[image_col]:
                            urls = [u.strip() for u in str(row[image_col]).split(",") if u.strip()]
                            for url in urls:
                                try:
                                    r = requests.get(url, timeout=10)
                                    if r.status_code == 200:
                                        filename = os.path.basename(url.split("?")[0]) or f"{external_id}.jpg"
                                        content = ContentFile(r.content)
                                        content.name = filename
                                        ItemPhoto.objects.create(item=item, image=content)
                                        image_found = True
                                except Exception:
                                    pass

                        if image_found:
                            item.is_approved = True
                            item.save(update_fields=["is_approved"])
                        else:
                            no_photo.append(external_id)

                    except Exception as e:
                        print(f"[ERROR] Row {row}: {e}")
                        failed += 1

                wb.close()

            # --- 2️⃣ ZIP-only upload (add photos to existing items) ----
            elif zip_file and not excel_file:
                # ✅ normalize external_ids from DB as well
                existing = {}
                for i in Item.objects.exclude(external_id__isnull=True).exclude(external_id__exact=""):
                    norm = normalize_external_id(i.external_id)
                    if norm:
                        existing[norm] = i

                for root, _, files in os.walk(photos_dir):
                    for filename in files:
                        filename_lower = filename.lower()
                        for external_id, item in existing.items():
                            if external_id and external_id.lower() in filename_lower:
                                try:
                                    with open(os.path.join(root, filename), "rb") as img_file:
                                        content = ContentFile(img_file.read())
                                        content.name = filename
                                        ItemPhoto.objects.create(item=item, image=content)
                                        added_photos += 1
                                        # optional: auto-approve once it has photos
                                        if not item.is_approved:
                                            item.is_approved = True
                                            item.save(update_fields=["is_approved"])
                                    break  # stop checking other external_ids for this file
                                except Exception as e:
                                    print(f"[ERROR] Failed saving photo {filename}: {e}")
                                    failed += 1
                                    break

            # --- Cleanup
            for p in [excel_path, zip_path]:
                if p and os.path.exists(p):
                    os.remove(p)

            msg = "✅ Import finished."
            if excel_path:
                msg += f" {created} created, {updated} updated, {failed} failed."
            if zip_file:
                msg += f" {added_photos} photos added."
            if no_photo:
                msg += f" ⚠️ {len(no_photo)} items without photos."
            self.message_user(request, msg, level=messages.SUCCESS)
            return redirect("../")

        # Default GET
        return render(
            request,
            "admin/import_excel.html",
            {"title": "Import Items (Excel and/or ZIP)"},
        )




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



@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "item__title", "message")


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
