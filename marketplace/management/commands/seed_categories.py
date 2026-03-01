"""
Management command to seed the initial category tree and download
category photos from Unsplash.

Structure:
    Root  (parent=None)  ← photo downloaded
    └── Sub  (parent=Root)  ← photo downloaded
        └── Leaf  (parent=Sub)  ← no specific photo

Run:
    python manage.py seed_categories
    python manage.py seed_categories --clear   # wipe & re-seed
    python manage.py seed_categories --skip-photos  # skip image downloads
"""

import os
import re

import requests
import urllib3
from django.core.files.base import ContentFile

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.core.management.base import BaseCommand

from marketplace.models import Category, CategoryPhoto


CATEGORIES = [
    {
        "name": "ركن العقارات",
        "icon": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "شقق للإيجار والبيع",
                "icon": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=300&h=300&fit=crop",
                "leaves": ["شقق عائلية", "استوديو عزاب", "دوبلكس", "شقق مفروشة", "شقق فاخرة", "نظام تمليك"],
            },
            {
                "name": "فلل وقصور",
                "icon": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=300&h=300&fit=crop",
                "leaves": ["فلل مودرن", "قصور كلاسيكية", "فلل مع مسبح", "فلل درج داخلي", "تاون هاوس"],
            },
            {
                "name": "أراضي ومزارع",
                "icon": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=300&h=300&fit=crop",
                "leaves": ["أراضي سكنية", "أراضي تجارية", "مزارع واستراحات", "مخططات جديدة"],
            },
        ],
    },
    {
        "name": "ركن الإلكترونيات",
        "icon": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "جوالات وتابلت",
                "icon": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&h=300&fit=crop",
                "leaves": ["آيفون 15", "سامسونج S24", "آيباد برو", "هواوي", "شاومي", "جوالات مستعملة", "إكسسوارات جوال"],
            },
            {
                "name": "كمبيوتر ولابتوب",
                "icon": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=300&h=300&fit=crop",
                "leaves": ["ماك بوك", "لابتوب جيمينج", "تجميعات PC", "شاشات 4K", "طابعات", "لوحات مفاتيح ميكانيكية"],
            },
            {
                "name": "ألعاب فيديو",
                "icon": "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?w=300&h=300&fit=crop",
                "leaves": ["بلايستيشن 5", "إكس بوكس", "نينتندو سويتش", "حسابات ألعاب", "كروت شحن"],
            },
        ],
    },
    {
        "name": "ركن الأثاث والديكورات",
        "icon": "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "غرف الجلوس",
                "icon": "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=300&h=300&fit=crop",
                "leaves": ["كنب مودرن", "طاولات قهوة", "سجاد إيراني", "ستائر", "ورق حائط", "إضاءات سقف", "مكتبات تلفزيون"],
            },
            {
                "name": "غرف النوم",
                "icon": "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=300&h=300&fit=crop",
                "leaves": ["أسرة مزدوجة", "خزائن ملابس", "مفارش", "مراتب طبية", "تسريحات", "غرف أطفال"],
            },
            {
                "name": "المطابخ",
                "icon": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=300&h=300&fit=crop",
                "leaves": ["خزائن مطبخ", "أدوات مائدة", "أجهزة طبخ", "طاولات طعام", "ميكرويف"],
            },
        ],
    },
    {
        "name": "ركن الوظائف",
        "icon": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "وظائف إدارية",
                "icon": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=300&h=300&fit=crop",
                "leaves": ["سكرتارية", "إدارة مشاريع", "موارد بشرية", "خدمة عملاء", "إدخال بيانات"],
            },
            {
                "name": "وظائف تقنية",
                "icon": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=300&h=300&fit=crop",
                "leaves": ["مطور ويب", "مطور تطبيقات", "دعم فني", "أمن معلومات", "تحليل بيانات"],
            },
        ],
    },
    {
        "name": "ركن الخدمات",
        "icon": "https://images.unsplash.com/photo-1521791055366-0d553872125f?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "خدمات منزلية",
                "icon": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=300&h=300&fit=crop",
                "leaves": ["سباكة", "كهرباء", "تنظيف منازل", "مكافحة حشرات", "نقل عفش"],
            },
            {
                "name": "خدمات مهنية",
                "icon": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=300&h=300&fit=crop",
                "leaves": ["تصميم جرافيك", "تصوير", "تسويق رقمي", "كتابة محتوى", "استشارات"],
            },
        ],
    },
    {
        "name": "ركن الحيوانات",
        "icon": "https://images.unsplash.com/photo-1517849845537-4d257902454a?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "حيوانات أليفة",
                "icon": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=300&h=300&fit=crop",
                "leaves": ["قطط", "كلاب", "طيور", "أسماك", "أرانب"],
            },
            {
                "name": "مستلزمات الحيوانات",
                "icon": "https://images.unsplash.com/photo-1558944351-cbb1b65f5f7a?w=300&h=300&fit=crop",
                "leaves": ["أطعمة", "أقفاص", "ألعاب", "رعاية صحية", "إكسسوارات"],
            },
        ],
    },
    {
        "name": "ركن الموضة والجمال",
        "icon": "https://images.unsplash.com/photo-1520974735194-9d8d3d8a5f53?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "ملابس",
                "icon": "https://images.unsplash.com/photo-1521334884684-d80222895322?w=300&h=300&fit=crop",
                "leaves": ["ملابس رجالية", "ملابس نسائية", "ملابس أطفال", "ملابس رياضية"],
            },
            {
                "name": "تجميل وعناية",
                "icon": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=300&h=300&fit=crop",
                "leaves": ["مكياج", "عطور", "عناية بالبشرة", "عناية بالشعر", "أدوات تجميل"],
            },
        ],
    },
    {
        "name": "ركن السفر والسياحة",
        "icon": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "رحلات وسياحة",
                "icon": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=300&h=300&fit=crop",
                "leaves": ["رحلات داخلية", "رحلات خارجية", "عروض سياحية", "حج وعمرة"],
            },
            {
                "name": "حجوزات",
                "icon": "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=300&h=300&fit=crop",
                "leaves": ["تذاكر طيران", "حجوزات فنادق", "تأجير سيارات", "تأمين سفر"],
            },
        ],
    },
    {
        "name": "ركن التعليم والتدريب",
        "icon": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "دورات تعليمية",
                "icon": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=300&h=300&fit=crop",
                "leaves": ["دورات أونلاين", "لغات", "برمجة", "تصميم", "إدارة أعمال"],
            },
            {
                "name": "خدمات تعليمية",
                "icon": "https://images.unsplash.com/photo-1513258496099-48168024aec0?w=300&h=300&fit=crop",
                "leaves": ["دروس خصوصية", "حل واجبات", "أبحاث جامعية", "استشارات تعليمية"],
            },
        ],
    },
    {
        "name": "ركن الرياضة والهوايات",
        "icon": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=300&h=300&fit=crop",
        "subs": [
            {
                "name": "معدات رياضية",
                "icon": "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=300&h=300&fit=crop",
                "leaves": ["أجهزة رياضية", "أدوات كمال أجسام", "ملابس رياضية", "مكملات غذائية"],
            },
            {
                "name": "هوايات",
                "icon": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=300&h=300&fit=crop",
                "leaves": ["تصوير", "رسم", "موسيقى", "ألعاب هواة", "تخييم"],
            },
        ],
    },
]


def _photo_filename(url):
    """Derive a safe filename from the Unsplash photo ID in the URL."""
    match = re.search(r"photo-([a-z0-9]+)", url)
    photo_id = match.group(1) if match else "unknown"
    return f"category_{photo_id}.jpg"


class Command(BaseCommand):
    help = "Seed the initial category tree and download Unsplash photos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete ALL existing categories before seeding",
        )
        parser.add_argument(
            "--skip-photos",
            action="store_true",
            help="Skip downloading and saving category photos",
        )

    def handle(self, *args, **options):
        skip_photos = options["skip_photos"]

        if options["clear"]:
            deleted, _ = Category.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing categories."))

        roots_created = subs_created = leaves_created = photos_saved = photos_failed = 0

        for root_data in CATEGORIES:
            root, created = Category.objects.get_or_create(
                name=root_data["name"],
                defaults={"parent": None},
            )
            if created:
                roots_created += 1

            if not skip_photos:
                ok = self._save_photo(root, root_data["icon"])
                if ok:
                    photos_saved += 1
                else:
                    photos_failed += 1

            for sub_data in root_data["subs"]:
                sub, created = Category.objects.get_or_create(
                    name=sub_data["name"],
                    defaults={"parent": root},
                )
                if created:
                    subs_created += 1

                if not skip_photos:
                    ok = self._save_photo(sub, sub_data["icon"])
                    if ok:
                        photos_saved += 1
                    else:
                        photos_failed += 1

                for leaf_name in sub_data["leaves"]:
                    _, created = Category.objects.get_or_create(
                        name=leaf_name,
                        defaults={"parent": sub},
                    )
                    if created:
                        leaves_created += 1

        total = roots_created + subs_created + leaves_created
        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {total} categories "
            f"({roots_created} roots, {subs_created} subs, {leaves_created} leaves)."
        ))
        if not skip_photos:
            self.stdout.write(self.style.SUCCESS(f"Photos saved: {photos_saved}  failed: {photos_failed}"))

    def _save_photo(self, category, url):
        """Download image from URL and attach it as CategoryPhoto. Returns True on success."""
        # Skip if a photo already exists for this category
        if CategoryPhoto.objects.filter(category=category).exists():
            return True

        try:
            response = requests.get(url, timeout=15, verify=False)
            response.raise_for_status()
        except Exception as exc:
            self.stderr.write(self.style.WARNING(f"  [WARN] Could not fetch {url}: {exc}"))
            return False

        filename = _photo_filename(url)
        photo = CategoryPhoto(category=category)
        photo.image.save(filename, ContentFile(response.content), save=True)

        self.stdout.write(f"  Saved photo for '{category.name}' → {os.path.basename(photo.image.name)}")
        return True
