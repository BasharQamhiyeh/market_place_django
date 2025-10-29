import os
import tempfile
import requests
import openpyxl
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.core.files import File
from django.conf import settings
from .models import Item, Category, ItemPhoto


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "category", "is_approved", "created_at")
    list_filter = ("category", "is_approved", "is_active")
    search_fields = ("title", "description")

    # Add a custom admin page for import
    change_list_template = "admin/items_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-excel/", self.admin_site.admin_view(self.import_excel_view), name="import_excel"),
        ]
        return custom_urls + urls

    def import_excel_view(self, request):
        if request.method == "POST":
            excel_file = request.FILES.get("excel_file")
            if not excel_file:
                self.message_user(request, "⚠️ Please upload an Excel file.", level=messages.WARNING)
                return redirect("..")

            # Save the uploaded file temporarily
            tmp_path = tempfile.mktemp(suffix=".xlsx")
            with open(tmp_path, "wb+") as dest:
                for chunk in excel_file.chunks():
                    dest.write(chunk)

            wb = openpyxl.load_workbook(tmp_path)
            sheet = wb.active
            created_count = 0
            failed_count = 0

            # Skip header row, start from row 2
            for row in sheet.iter_rows(min_row=2, values_only=True):
                try:
                    name_ar = row[1]       # Arabic name
                    name_en = row[2]       # English name (optional)
                    desc_ar = row[3]       # Arabic description
                    desc_en = row[4]       # English description
                    price = row[5]
                    image_url = row[12]    # URL column
                    category_name = row[13]

                    if not name_ar or not price or not category_name:
                        continue

                    # Find or create category
                    category, _ = Category.objects.get_or_create(name_ar=category_name, defaults={'name_en': category_name})

                    # Create item
                    item = Item.objects.create(
                        title=name_ar,
                        description=desc_ar or name_en or "",
                        price=float(price),
                        category=category,
                        user=request.user,  # imported by admin
                        is_approved=True,
                        is_active=True,
                    )

                    # Download and attach image
                    if image_url and image_url.startswith("http"):
                        try:
                            response = requests.get(image_url, timeout=10)
                            if response.status_code == 200:
                                tmp_img = tempfile.NamedTemporaryFile(delete=True)
                                tmp_img.write(response.content)
                                tmp_img.flush()
                                photo = ItemPhoto(item=item)
                                photo.image.save(os.path.basename(image_url), File(tmp_img))
                                tmp_img.close()
                        except Exception as e:
                            print(f"[WARN] Could not fetch image for {name_ar}: {e}")

                    created_count += 1

                except Exception as e:
                    print(f"[ERROR] Failed to import row: {e}")
                    failed_count += 1

            wb.close()
            os.remove(tmp_path)
            self.message_user(
                request,
                f"✅ Import finished: {created_count} items created, {failed_count} failed.",
                level=messages.SUCCESS
            )
            return redirect("..")

        context = {"title": "Import Items from Excel"}
        return render(request, "admin/import_excel.html", context)
