"""
Creates minimal test data (categories + approved items + requests) so that
the search suggestions can be tested locally.

Usage:
    python manage.py seed_test_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from marketplace.models import Category, Item, Listing, User
from marketplace.models.requests import Request


CATEGORIES = [
    "إلكترونيات",
    "سيارات",
    "عقارات",
    "ملابس",
    "أثاث",
]

ITEMS = [
    ("آيفون 14 برو للبيع", "إلكترونيات", 800.0),
    ("سامسونج جالاكسي S23", "إلكترونيات", 650.0),
    ("لابتوب ديل للبيع", "إلكترونيات", 500.0),
    ("سيارة تويوتا كامري 2020", "سيارات", 15000.0),
    ("سيارة هوندا سيفيك مستعملة", "سيارات", 9000.0),
    ("شقة للبيع عمان", "عقارات", 75000.0),
    ("طاولة طعام خشبية", "أثاث", 200.0),
    ("كرسي مكتبي", "أثاث", 80.0),
]

REQUESTS = [
    ("أبحث عن آيفون 13", "إلكترونيات", 500.0),
    ("مطلوب سيارة كيا", "سيارات", 8000.0),
    ("أبحث عن لابتوب مستعمل", "إلكترونيات", 300.0),
]


class Command(BaseCommand):
    help = "Seed test categories, items, and requests for local development"

    def handle(self, *args, **options):
        # get or create a test user
        user = User.objects.filter(username="testuser").first()
        if not user:
            user = User.objects.create_user(
                username="testuser",
                phone="0790000000",
                password="testpass123",
            )
            self.stdout.write(f"  Created user: testuser (phone=0790000000)")
        else:
            self.stdout.write(f"  Using existing user: {user.username}")

        # categories
        cat_map = {}
        for name in CATEGORIES:
            cat, created = Category.objects.get_or_create(name=name)
            cat_map[name] = cat
            if created:
                self.stdout.write(f"  Created category: {name}")

        # items
        for title, cat_name, price in ITEMS:
            if Listing.objects.filter(title=title).exists():
                self.stdout.write(f"  Skipped (exists): {title}")
                continue
            with transaction.atomic():
                listing = Listing.objects.create(
                    type="item",
                    user=user,
                    category=cat_map[cat_name],
                    title=title,
                    description=f"وصف تجريبي لـ {title}",
                    is_active=True,
                    is_approved=True,
                    approved_at=timezone.now(),
                    published_at=timezone.now(),
                )
                Item.objects.create(listing=listing, price=price, condition="used")
            self.stdout.write(f"  Created item: {title}")

        # requests
        for title, cat_name, budget in REQUESTS:
            if Listing.objects.filter(title=title).exists():
                self.stdout.write(f"  Skipped (exists): {title}")
                continue
            with transaction.atomic():
                listing = Listing.objects.create(
                    type="request",
                    user=user,
                    category=cat_map[cat_name],
                    title=title,
                    description=f"وصف تجريبي لـ {title}",
                    is_active=True,
                    is_approved=True,
                    approved_at=timezone.now(),
                    published_at=timezone.now(),
                )
                Request.objects.create(listing=listing, budget=budget, condition_preference="any")
            self.stdout.write(f"  Created request: {title}")

        self.stdout.write(self.style.SUCCESS("\nDone! Search for 'آيفون' or 'سيارة' to test."))
