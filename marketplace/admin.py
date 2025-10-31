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
        Import items from Excel (.xlsx) and photos from ZIP or URLs.
        Priority:
          1️⃣ Photos from ZIP file (matched by external_id substring)
          2️⃣ If none found, use URLs in 'image' column.
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

            excel_path = tempfile.mktemp(suffix=".xlsx")
            zip_path = tempfile.mktemp(suffix=".zip")
            photos_dir = tempfile.mkdtemp()

            with open(excel_path, "wb+") as f:
                for chunk in excel_file.chunks():
                    f.write(chunk)
            with open(zip_path, "wb+") as f:
                for chunk in zip_file.chunks():
                    f.write(chunk)

            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(photos_dir)
            except Exception as e:
                self.message_user(request, f"❌ Failed to extract ZIP: {e}", level=messages.ERROR)
                return redirect("..")

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
            image_col = col("image") or col("images")

            required = [id_col, name_col, price_col, category_col]
            if any(c is None for c in required):
                missing = [n for n, c in zip(["id", "name", "price", "category"], required) if c is None]
                self.message_user(request, f"❌ Missing required columns: {', '.join(missing)}", level=messages.ERROR)
                return redirect("..")

            created_count, failed_count = 0, 0
            missing_images = []

            for row in sheet.iter_rows(min_row=2, values_only=True):
                try:
                    external_id = str(int(row[id_col])).strip() if row[id_col] else None
                    title = str(row[name_col]).strip() if row[name_col] else None
                    desc = str(row[desc_col]).strip() if desc_col is not None and row[desc_col] else ""
                    price = float(row[price_col]) if row[price_col] else None
                    category_name = str(row[category_col]).strip() if row[category_col] else None
                    image_urls = str(row[image_col]).strip() if image_col is not None and row[image_col] else ""

                    if not external_id or not title or not price or not category_name:
                        continue

                    category, _ = Category.objects.get_or_create(
                        name_ar=category_name,
                        defaults={"name_en": category_name}
                    )

                    item = Item.objects.create(
                        title=title,
                        description=desc,
                        price=price,
                        category=category,
                        user=request.user,
                        is_approved=True,
                        is_active=True,
                    )

                    # --- Try ZIP photos first
                    image_found = False
                    for root, _, files in os.walk(photos_dir):
                        for filename in files:
                            if external_id.lower() in filename.lower():  # relaxed matching
                                file_path = os.path.join(root, filename)
                                try:
                                    with open(file_path, "rb") as img_file:
                                        content = ContentFile(img_file.read())
                                        photo = ItemPhoto(item=item)
                                        photo.image.save(os.path.basename(filename), content, save=True)
                                    image_found = True
                                    print(f"[INFO] Added ZIP image for {external_id}: {filename}")
                                except Exception as e:
                                    print(f"[WARN] Could not save ZIP image {filename}: {e}")

                    # --- Fallback to URLs
                    if not image_found and image_urls:
                        urls = [u.strip() for u in image_urls.replace("\n", ",").replace(" ", ",").split(",") if
                                u.strip()]
                        for url in urls:
                            if not url.startswith("http"):
                                continue
                            try:
                                resp = requests.get(url, timeout=10)
                                if resp.status_code == 200:
                                    filename = os.path.basename(url.split("?")[0]) or f"{external_id}.jpg"
                                    content = ContentFile(resp.content)
                                    photo = ItemPhoto(item=item)
                                    photo.image.save(filename, content, save=True)
                                    image_found = True
                                    print(f"[INFO] Downloaded image for {external_id} from {url}")
                                else:
                                    print(f"[WARN] Bad status {resp.status_code} for {url}")
                            except Exception as e:
                                print(f"[WARN] Failed to fetch image from {url}: {e}")

                    if not image_found:
                        missing_images.append(external_id)

                    created_count += 1

                except Exception as e:
                    print(f"[ERROR] Row import failed for {row}: {e}")
                    failed_count += 1

            wb.close()
            os.remove(excel_path)
            os.remove(zip_path)

            summary = f"✅ Import finished: {created_count} items created, {failed_count} failed."
            if missing_images:
                summary += f" ⚠️ {len(missing_images)} items had no photos."
            self.message_user(request, summary, level=messages.SUCCESS)
            return redirect("../")

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

