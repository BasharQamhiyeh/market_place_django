from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE,
        related_name="subcategories", null=True, blank=True
    )

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
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class CategoryPhoto(models.Model):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name="photo", null=True, blank=True,)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.category.name}"


class Attribute(models.Model):
    INPUT_TYPE_CHOICES = [('text', 'Text'), ('number', 'Number'), ('select', 'Select')]
    UI_TYPE_CHOICES = [
        ('dropdown', 'Dropdown'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox List'),
        ('single_checkbox', 'Single Checkbox'),
        ('tags', 'Tags / Multi-Select'),
    ]

    name = models.CharField(max_length=255)
    input_type = models.CharField(max_length=50, choices=INPUT_TYPE_CHOICES, default='text')
    ui_type = models.CharField(max_length=50, choices=UI_TYPE_CHOICES, blank=True, null=True)

    is_required = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="attributes")

    def __str__(self):
        return self.name


class AttributeOption(models.Model):
    value = models.CharField(max_length=255)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="options")

    def __str__(self):
        return self.value