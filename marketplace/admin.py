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
        Admin-only import of items from an Excel (.xlsx) file.
        Expected columns (0-based index in the active sheet):
            row[1]  -> Name (Arabic)        -> Item.title
            row[3]  -> Description (Arabic) -> Item.description (fallback to EN ok)
            row[5]  -> Price                -> Item.price
            row[12] -> Image URLs           -> one or multiple http links in the same cell
            row[13] -> Category Name (AR)   -> Category by name_ar (create if missing)
        """
        if request.method == "POST":
            excel_file = request.FILES.get("excel_file")
            if not excel_file:
                self.message_user(request, "⚠️ Please upload an Excel file.", level=messages.WARNING)
                return redirect("..")

            # Save upload to a temp file
            tmp_path = tempfile.mktemp(suffix=".xlsx")
            with open(tmp_path, "wb+") as dest:
                for chunk in excel_file.chunks():
                    dest.write(chunk)

            # Parse workbook
            wb = openpyxl.load_workbook(tmp_path)
            sheet = wb.active
            created_count = 0
            failed_count = 0

            for row in sheet.iter_rows(min_row=2, values_only=True):
                try:
                    name_ar = row[1]  # Arabic Name
                    desc_ar = row[3]  # Arabic Description
                    price = row[5]  # Price
                    image_urls = row[11]  # One or multiple URLs
                    category_name = row[12]  # Arabic category name

                    if not name_ar or not price or not category_name:
                        continue

                    # Find or create category by Arabic name
                    category, _ = Category.objects.get_or_create(
                        name_ar=category_name,
                        defaults={'name_en': category_name}
                    )

                    # Create the item
                    item = Item.objects.create(
                        title=name_ar,
                        description=desc_ar or "",
                        price=float(price),
                        category=category,
                        user=request.user,  # the admin importing
                        is_approved=True,  # imported items start as approved (tweak if needed)
                        is_active=True,
                    )

                    # Multiple image URLs in the same cell -> split by comma/space/newline
                    if image_urls:
                        if isinstance(image_urls, str):
                            urls = [u.strip() for u in image_urls.replace("\n", ",").replace(" ", ",").split(",") if
                                    u.strip()]
                        else:
                            urls = [str(image_urls)]

                        for url in urls:
                            if not url.startswith("http"):
                                continue
                            try:
                                resp = requests.get(url, timeout=10)
                                if resp.status_code == 200:
                                    tmp_img = tempfile.NamedTemporaryFile(delete=True)
                                    tmp_img.write(resp.content)
                                    tmp_img.flush()
                                    photo = ItemPhoto(item=item)
                                    # safe filename
                                    img_name = os.path.basename(url.split("?")[0]) or f"photo_{item.id}.jpg"
                                    photo.image.save(img_name, File(tmp_img))
                                    tmp_img.close()
                            except Exception as e:
                                print(f"[WARN] Image fetch failed for '{name_ar}': {e}")

                    created_count += 1

                except Exception as e:
                    print(f"[ERROR] Row import failed: {e}")
                    failed_count += 1

            wb.close()
            os.remove(tmp_path)

            self.message_user(
                request,
                f"✅ Import finished: {created_count} items created, {failed_count} failed.",
                level=messages.SUCCESS
            )
            return redirect("../")  # back to Item list

        # GET -> render upload form
        return render(request, "admin/import_excel.html", {"title": "Import Items from Excel"})




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

