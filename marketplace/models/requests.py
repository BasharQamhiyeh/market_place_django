from django.db import models

from marketplace.models import Listing, Attribute


class Request(models.Model):
    CONDITION_CHOICES = [
        ("any", "لا يهم"),
        ("new", "جديد"),
        ("used", "مستعمل"),
    ]

    listing = models.OneToOneField(Listing, on_delete=models.CASCADE, related_name="request")

    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition_preference = models.CharField(max_length=10, choices=CONDITION_CHOICES, default="any")

    def __str__(self):
        return self.listing.title


class RequestAttributeValue(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.attribute} = {self.value or '(no preference)'}"