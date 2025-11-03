from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect, render
from django.contrib.admin.views.main import IS_POPUP_VAR
from django.utils.html import format_html
from django.db import models
from django.core.files.base import ContentFile
import tempfile, os, zipfile, openpyxl
from django.urls import reverse

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


import nested_admin
from django.contrib import admin
from .models import Category, Attribute, AttributeOption


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
    list_display = ("id", "name_en", "name_ar", "parent")
    search_fields = ("name_en", "name_ar")
    list_filter = ("parent",)
    inlines = [AttributeInline]



# ======================================================
# ✅ ITEM ADMIN — cleaned, color-coded, review-based
# ======================================================
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    change_form_template = "admin/marketplace/item/change_form.html"
    change_list_template = "admin/items_changelist.html"

    list_display = (
        "id", "title", "category", "price",
        "get_username", "get_first_name", "get_last_name",
        "colored_status", "created_at", "condition", "is_active"
    )
    readonly_fields = ("colored_status", "photo_gallery")
    list_filter = ("category", "user", "is_active", "is_approved", "condition")
    search_fields = ("title", "user__username", "category__name_en", "category__name_ar", "user__first_name", "user__last_name", "user__email", "user__phone")
    actions = []

    fields = (
        "title",
        "category",
        "price",
        "condition",
        "description",  # ✅ inserted here
        "photo_gallery",
        "user",
        "colored_status",
    )

    # def rendered_description(self, obj):
    #     """Show formatted description in admin."""
    #     if obj.description:
    #         return format_html(obj.description)
    #     return "-"
    #
    # rendered_description.short_description = "Description (Rendered HTML)"

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
    # Approve view
    # -----------------------------
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

        self.message_user(request, "✅ Item approved & user notified.", messages.SUCCESS)
        return redirect(f"../../{item_id}/change/")

    # -----------------------------
    # Reject view (with reason)
    # -----------------------------
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

            self.message_user(request, "❌ Item rejected & user notified.", messages.ERROR)
            return redirect(f"../../{item_id}/change/")

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

    def photo_gallery(self, obj):
        photos = obj.photos.all()
        if not photos:
            return "No photos uploaded."
        html = "".join([
            f'<img src="{p.image.url}" style="width:160px;border-radius:8px;margin:4px;">'
            for p in photos
        ])
        return format_html(html)

    photo_gallery.short_description = "Item Photos"

    # -----------------------------
    # Import Items (Excel + ZIP)
    # -----------------------------
    def import_excel_view(self, request):
        """
        Import items from Excel (.xlsx) + photos ZIP.
        Each row: id, name, description, price, category, subcategory?, city?
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

            # --- Extract ZIP
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
            subcategory_col = col("subcategory")
            city_col = col("city")

            required = [id_col, name_col, price_col, category_col]
            if any(c is None for c in required):
                missing = [n for n, c in zip(["id", "name", "price", "category"], required) if c is None]
                self.message_user(request, f"❌ Missing columns: {', '.join(missing)}", level=messages.ERROR)
                return redirect("..")

            created, failed, no_photo = 0, 0, []

            for row in sheet.iter_rows(min_row=2, values_only=True):
                try:
                    external_id = str(int(row[id_col])).strip() if row[id_col] else None
                    title = str(row[name_col]).strip() if row[name_col] else None
                    desc = str(row[desc_col]).strip() if desc_col and row[desc_col] else ""
                    price = float(row[price_col]) if row[price_col] else None
                    category_name = str(row[category_col]).strip() if row[category_col] else None
                    subcategory_name = (
                        str(row[subcategory_col]).strip() if subcategory_col and row[subcategory_col] else None
                    )
                    city_name = str(row[city_col]).strip() if city_col and row[city_col] else None

                    if not external_id or not title or not price or not category_name:
                        continue

                    # --- Category & subcategory
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

                    # --- Find photos
                    image_found = False
                    for root, _, files in os.walk(photos_dir):
                        for filename in files:
                            if external_id.lower() in filename.lower():
                                image_found = True
                                break
                        if image_found:
                            break

                    # --- Create item
                    item = Item.objects.create(
                        title=title,
                        description=desc,
                        price=price,
                        category=assigned_category,
                        city=city,
                        user=request.user,
                        is_active=True,
                        is_approved=image_found,
                        condition="new",
                    )

                    # --- Save images
                    for root, _, files in os.walk(photos_dir):
                        for filename in files:
                            if external_id.lower() in filename.lower():
                                try:
                                    with open(os.path.join(root, filename), "rb") as img_file:
                                        content = ContentFile(img_file.read())
                                        content.name = filename
                                        ItemPhoto.objects.create(item=item, image=content)
                                except Exception as e:
                                    print(f"[WARN] Could not save {filename}: {e}")

                    if not image_found:
                        no_photo.append(external_id)
                    created += 1

                except Exception as e:
                    print(f"[ERROR] Failed row {row}: {e}")
                    failed += 1

            wb.close()
            os.remove(excel_path)
            os.remove(zip_path)

            msg = f"✅ Import finished: {created} items created, {failed} failed."
            if no_photo:
                msg += f" ⚠️ {len(no_photo)} without photos (not approved)."
            self.message_user(request, msg, level=messages.SUCCESS)
            return redirect("../")

        return render(request, "admin/import_excel.html", {"title": "Import Items from Excel & ZIP"})


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
    list_display = ("id", "name_en", "name_ar", "is_active")
    search_fields = ("name_en", "name_ar")
    list_filter = ("is_active",)


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
admin.site.site_header = "Souq Jordan Administration"
admin.site.index_title = "Control Panel"
admin.site.site_title = "Souq Jordan Admin"
