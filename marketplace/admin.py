from django.contrib import admin
from .models import (
    User,
    Category,
    Attribute,
    AttributeOption,
    Item,
    ItemAttributeValue,
    ItemPhoto
)


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


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "price", "user", "created_at", "is_active", "is_approved")
    list_filter = ("category", "user", "is_active", "is_approved")
    actions = ["approve_items", "deactivate_items"]

    @admin.action(description="Approve selected items")
    def approve_items(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Deactivate selected items")
    def deactivate_items(self, request, queryset):
        queryset.update(is_active=False)


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




