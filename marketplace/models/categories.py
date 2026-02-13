from django.db import models


class Category(models.Model):
    name_en = models.CharField(max_length=255, unique=True)
    name_ar = models.CharField(max_length=255, unique=True)
    child_label = models.CharField(max_length=255, blank=True, null=True)
    subtitle_en = models.CharField(max_length=255, blank=True, null=True)
    subtitle_ar = models.CharField(max_length=255, blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="subcategories", null=True, blank=True)

    @property
    def photo_url(self):
        p = getattr(self, "photo", None)
        if p and getattr(p, "image", None):
            try:
                return p.image.url
            except Exception:
                return None
        return None

    def __str__(self):
        from django.utils import translation
        return self.name_ar if translation.get_language() == "ar" else self.name_en

    class Meta:
        verbose_name_plural = "Categories"


class CategoryPhoto(models.Model):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name="photo")
    image = models.ImageField(upload_to="categories/")  # ✅ uses your configured storage
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.category.name_ar}"


class Attribute(models.Model):
    INPUT_TYPE_CHOICES = [('text', 'Text'), ('number', 'Number'), ('select', 'Select')]
    UI_TYPE_CHOICES = [
        ('dropdown', 'Dropdown'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox List'),
        ('single_checkbox', 'Single Checkbox'),
        ('tags', 'Tags / Multi-Select'),
    ]

    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255)
    input_type = models.CharField(max_length=50, choices=INPUT_TYPE_CHOICES, default='text')
    ui_type = models.CharField(max_length=50, choices=UI_TYPE_CHOICES, default='dropdown')
    is_required = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="attributes")

    def __str__(self):
        from django.utils import translation
        return self.name_ar if translation.get_language() == 'ar' else self.name_en


class AttributeOption(models.Model):
    value_en = models.CharField(max_length=255)
    value_ar = models.CharField(max_length=255)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="options")

    def __str__(self):
        from django.utils import translation
        return self.value_ar if translation.get_language() == 'ar' else self.value_en