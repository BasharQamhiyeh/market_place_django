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

    # Extra URLs
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:item_id>/approve/", self.admin_site.admin_view(self.approve_view),
                 name="item_approve"),
            path("<int:item_id>/reject/", self.admin_site.admin_view(self.reject_view),
                 name="item_reject"),
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

