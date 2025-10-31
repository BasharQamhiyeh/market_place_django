from django.contrib import admin, messages
from .models import (
    User,
    Category,
    Attribute,
    AttributeOption,
    Item,
    ItemAttributeValue,
    ItemPhoto,
    Notification,
    City
)
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.contrib.admin.views.main import IS_POPUP_VAR
import tempfile, requests, openpyxl, os
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import zipfile
from django.db import models


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "username", "phone", "email", "is_staff")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name_en", "name_ar", "description")
    search_fields = ("name_en", "name_ar")
    list_filter = ("name_en",)


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("id", "name_en", "name_ar", "category", "input_type", "is_required")
    search_fields = ("name_en", "name_ar")
    list_filter = ("category", "is_required")


@admin.register(AttributeOption)
class AttributeOptionAdmin(admin.ModelAdmin):
    list_display = ("id", "value_en", "value_ar", "attribute")
    search_fields = ("value_en", "value_ar")
    list_filter = ("attribute",)


# marketplace/admin.py
from django.contrib import admin
from .models import (
    User, Category, Attribute, AttributeOption,
    Item, ItemAttributeValue, ItemPhoto, Notification
)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    change_form_template = "admin/marketplace/item/change_form.html"

    list_display = ("id", "title", "category", "price", "user", "created_at",
                    "condition", "is_active", "is_approved", "moderate_actions", "photo_gallery")
    list_filter = ("category", "user", "is_active", "is_approved", "condition")
    actions = ["approve_items", "reject_items", "deactivate_items"]

    readonly_fields = ("photo_gallery",)

    change_list_template = "admin/items_changelist.html"

    # Extra URLs
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:item_id>/approve/", self.admin_site.admin_view(self.approve_view),
                 name="item_approve"),
            path("<int:item_id>/reject/", self.admin_site.admin_view(self.reject_view),
                 name="item_reject"),
            path("import-excel/", self.admin_site.admin_view(self.import_excel_view),
                 name="marketplace_item_import_excel"),
        ]
        return custom + urls

    # Change page approve
    def approve_view(self, request, item_id):
        item = Item.objects.get(id=item_id)
        item.is_approved = True
        item.is_active = True
        item.save()

        Notification.objects.create(
            user=item.user,
            title="✅ تمت الموافقة على إعلانك",
            body=f"إعلانك '{item.title}' أصبح فعالاً الآن.",
            item=item,
        )

        self.message_user(request, "Item approved & user notified.", messages.SUCCESS)
        return redirect(f"../../{item_id}/change/")

    # Change page reject
    def reject_view(self, request, item_id):
        item = Item.objects.get(id=item_id)

        if request.method == "POST":
            reason = request.POST.get("reason") or "غير مذكور"

            item.is_approved = False
            item.is_active = False
            item.save()

            Notification.objects.create(
                user=item.user,
                title="❌ تم رفض إعلانك",
                body=f"إعلانك '{item.title}' تم رفضه. الأسباب: {reason}",
                item=item,
            )

            self.message_user(request, "Item rejected & user notified.", messages.ERROR)
            return redirect(f"../../{item_id}/change/")

        # ✅ admin context fix
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

    # Approve/Reject inline column
    def moderate_actions(self, obj):
        return format_html(
            f'<a class="button" href="{obj.id}/approve/" '
            f'style="margin-right:8px;color:green;font-weight:600;">Approve</a>'
            f'<a class="button" href="{obj.id}/reject/" '
            f'style="color:red;font-weight:600;">Reject</a>'
        )
    moderate_actions.short_description = "Moderation"

    # Bulk approve
    @admin.action(description="Approve selected items")
    def approve_items(self, request, queryset):
        for item in queryset:
            if not item.is_approved:
                item.is_approved = True
                item.is_active = True
                item.save()
                Notification.objects.create(
                    user=item.user,
                    title="✅ تمت الموافقة على إعلانك",
                    body=f"إعلانك '{item.title}' أصبح فعالاً الآن.",
                    item=item
                )
        self.message_user(request, f"Approved {queryset.count()} items and notified owners.")

    # Bulk reject
    @admin.action(description="Reject selected items")
    def reject_items(self, request, queryset):
        reason = request.POST.get('action_reason', '')
        for item in queryset:
            item.is_approved = False
            item.is_active = False
            item.save()
            Notification.objects.create(
                user=item.user,
                title="❌ تم رفض إعلانك",
                body=f"إعلانك '{item.title}' تم رفضه. الأسباب: {reason or 'غير مذكور'}",
                item=item
            )
        self.message_user(request, f"Rejected {queryset.count()} items and notified owners.")

    @admin.action(description="Deactivate selected items")
    def deactivate_items(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} items.")

    def photo_gallery(self, obj):
        photos = obj.photos.all()
        if not photos:
            return "No photos uploaded."

        html = ""
        for p in photos:
            html += f'<img src="{p.image.url}" style="width:120px;border-radius:6px;margin:4px;">'
        return format_html(html)

    photo_gallery.short_description = "Item Photos"

    def import_excel_view(self, request):
        """
        Import items from an Excel (.xlsx) file and photos from a ZIP file.

        Rules:
        - Excel columns (case-insensitive): id, name, description, price, category, city
        - ZIP may contain nested folders.
        - Match photos by filename containing external_id.
        - If no photos found → item not approved.
        - All imported items → condition='new'.
        - If city doesn't exist → create it.
        """
        if request.method == "POST":
            excel_file = request.FILES.get("excel_file")
            zip_file = request.FILES.get("zip_file")

            if not excel_file or not zip_file:
                self.message_user(request, "⚠️ Please upload both Excel and ZIP files.", level=messages.WARNING)
                return redirect("..")

            if not zip_file.name.lower().endswith(".zip"):
                self.message_user(request, "❌ Only .zip files are supported.", level=messages.ERROR)
                return redirect("..")

            # --- Temporary files setup
            excel_path = tempfile.mktemp(suffix=".xlsx")
            zip_path = tempfile.mktemp(suffix=".zip")
            photos_dir = tempfile.mkdtemp()

            with open(excel_path, "wb+") as f:
                for chunk in excel_file.chunks():
                    f.write(chunk)
            with open(zip_path, "wb+") as f:
                for chunk in zip_file.chunks():
                    f.write(chunk)

            # --- Extract ZIP
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(photos_dir)
            except Exception as e:
                self.message_user(request, f"❌ Failed to extract ZIP: {e}", level=messages.ERROR)
                return redirect("..")

            # --- Parse Excel
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
            city_col = col("city")

            required = [id_col, name_col, price_col, category_col]
            if any(c is None for c in required):
                missing = [n for n, c in zip(["id", "name", "price", "category"], required) if c is None]
                self.message_user(request, f"❌ Missing required columns: {', '.join(missing)}", level=messages.ERROR)
                return redirect("..")

            created_count = 0
            failed_count = 0
            no_photo_items = []

            # --- Import rows
            for row in sheet.iter_rows(min_row=2, values_only=True):
                try:
                    external_id = str(int(row[id_col])).strip() if row[id_col] else None
                    title = str(row[name_col]).strip() if row[name_col] else None
                    desc = str(row[desc_col]).strip() if desc_col is not None and row[desc_col] else ""
                    price = float(row[price_col]) if row[price_col] else None
                    category_name = str(row[category_col]).strip() if row[category_col] else None
                    city_name = str(row[city_col]).strip() if city_col is not None and row[city_col] else None

                    if not external_id or not title or not price or not category_name:
                        continue

                    # --- Category
                    category, _ = Category.objects.get_or_create(
                        name_ar=category_name,
                        defaults={'name_en': category_name}
                    )

                    # --- City (optional)
                    city = None
                    if city_name:
                        # Clean up the value
                        city_name = city_name.strip()

                        # Try to find by Arabic or English name, case-insensitive
                        city = City.objects.filter(
                            models.Q(name_ar__iexact=city_name) | models.Q(name_en__iexact=city_name)
                        ).first()

                        # If not found → create new one with both Arabic and English names equal
                        if not city:
                            city = City.objects.create(
                                name_ar=city_name,
                                name_en=city_name,
                            )

                    # --- Find photos
                    image_found = False
                    for root, _, files in os.walk(photos_dir):
                        for filename in files:
                            if external_id.lower() in filename.lower():
                                image_found = True
                                break
                        if image_found:
                            break

                    # --- Create Item
                    item = Item.objects.create(
                        title=title,
                        description=desc,
                        price=price,
                        category=category,
                        city=city,  # ✅ new
                        user=request.user,
                        is_active=True,
                        is_approved=image_found,  # only approved if photo exists
                        condition="new",  # ✅ always new
                    )

                    # --- Attach ZIP photos
                    for root, _, files in os.walk(photos_dir):
                        for filename in files:
                            if external_id.lower() in filename.lower():
                                file_path = os.path.join(root, filename)
                                try:
                                    with open(file_path, "rb") as img_file:
                                        content = ContentFile(img_file.read())
                                        photo = ItemPhoto(item=item)
                                        photo.image.save(os.path.basename(filename), content, save=True)
                                except Exception as e:
                                    print(f"[WARN] Could not save image {filename}: {e}")

                    if not image_found:
                        no_photo_items.append(external_id)

                    created_count += 1

                except Exception as e:
                    print(f"[ERROR] Row import failed for {row}: {e}")
                    failed_count += 1

            wb.close()
            os.remove(excel_path)
            os.remove(zip_path)

            summary = f"✅ Import finished: {created_count} items created, {failed_count} failed."
            if no_photo_items:
                summary += f" ⚠️ {len(no_photo_items)} items had no photos (not approved)."

            self.message_user(request, summary, level=messages.SUCCESS)
            return redirect("../")

        # --- GET → render upload form
        return render(request, "admin/import_excel.html", {"title": "Import Items from Excel & ZIP"})



@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("title", "body", "user__username")

# keep your other @admin.register classes (User, Category, Attribute, AttributeOption, ItemAttributeValue, ItemPhoto) as-is



@admin.register(ItemAttributeValue)
class ItemAttributeValueAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "attribute", "value")
    search_fields = ("value",)
    list_filter = ("attribute",)


@admin.register(ItemPhoto)
class ItemPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "image", "created_at")
    list_filter = ("item",)
    search_fields = ("item__title",)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name_en", "name_ar", "is_active")
    search_fields = ("name_en", "name_ar")
    list_filter = ("is_active",)


from .models import Favorite  # add to the big import list if not present

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "item__title")

