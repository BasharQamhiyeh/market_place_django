from django.db import models


class City(models.Model):
    name_en = models.CharField(max_length=150, unique=True)
    name_ar = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ["name_en"]

    def __str__(self):
        from django.utils import translation
        return self.name_ar if translation.get_language() == "ar" else self.name_en