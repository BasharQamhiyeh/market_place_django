from io import BytesIO

from PIL import ImageOps, ImageFilter
from PIL.Image import Image
from django.core.files.base import ContentFile
from django.db import models

from marketplace.models import Attribute


class Item(models.Model):
    CONDITION_CHOICES = [('new', 'New'), ('used', 'Used')]

    listing = models.OneToOneField("Listing", on_delete=models.CASCADE, related_name="item")

    price = models.FloatField()
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used')

    sold_on_site = models.BooleanField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True, null=True)

    external_id = models.CharField(max_length=64, null=True, blank=True, unique=True, db_index=True)

    auto_rejected = models.BooleanField(default=False)
    moderation_reason = models.TextField(blank=True, null=True)

    @property
    def main_photo(self):
        main = self.photos.filter(is_main=True).first()
        return main or self.photos.order_by('id').first()

    def __str__(self):
        return self.listing.title


# Single normalized target (16:10)
NORMAL_W = 1600
NORMAL_H = 1000


class ItemPhoto(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='items/')  # original
    normalized = models.ImageField(upload_to='items/normalized/', blank=True, null=True)  # ✅ single normalized
    created_at = models.DateTimeField(auto_now_add=True)
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"Photo for {self.item.listing.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # generate once (or regenerate if original changed and normalized missing)
        if self.image and not self.normalized:
            self.generate_normalized()

    def generate_normalized(self):
        """
        Create a single normalized image:
        - exact size NORMAL_W x NORMAL_H
        - FULL image visible (no crop)
        - no empty space (filled with blurred background)
        """
        try:
            # open from storage
            self.image.open("rb")
            im = Image.open(self.image)
            im = ImageOps.exif_transpose(im)  # fix rotation from phone photos
            im = im.convert("RGB")

            # background: cover then blur (fills full canvas)
            bg = ImageOps.fit(im, (NORMAL_W, NORMAL_H), method=Image.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(28))

            # foreground: contain (no crop)
            fg = ImageOps.contain(im, (NORMAL_W, NORMAL_H), method=Image.LANCZOS)

            # paste centered
            x = (NORMAL_W - fg.width) // 2
            y = (NORMAL_H - fg.height) // 2
            bg.paste(fg, (x, y))

            # write to buffer
            buf = BytesIO()
            bg.save(buf, format="JPEG", quality=85, optimize=True, progressive=True)

            base = self.image.name.split("/")[-1]
            name = f"norm_{base.rsplit('.', 1)[0]}.jpg"

            self.normalized.save(name, ContentFile(buf.getvalue()), save=False)
            super().save(update_fields=["normalized"])

        except Exception as e:
            print("Normalized image generation failed:", e)
        finally:
            try:
                self.image.close()
            except Exception:
                pass


class ItemAttributeValue(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='attribute_values')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.attribute}: {self.value}"