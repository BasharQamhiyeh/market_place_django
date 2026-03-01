"""
Management command to seed the initial category tree.

Structure:
    Root  (parent=None)
    └── Sub  (parent=Root)
        └── Leaf  (parent=Sub)

Run:
    python manage.py seed_categories
    python manage.py seed_categories --clear   # wipe & re-seed
"""

from django.core.management.base import BaseCommand

from marketplace.models import Category


CATEGORIES = [
    {
        "name": "ركن العقارات",
        "subs": [
            {
                "name": "شقق للإيجار والبيع",
                "leaves": ["شقق عائلية", "استوديو عزاب", "دوبلكس", "شقق مفروشة", "شقق فاخرة", "نظام تمليك"],
            },
            {
                "name": "فلل وقصور",
                "leaves": ["فلل مودرن", "قصور كلاسيكية", "فلل مع مسبح", "فلل درج داخلي", "تاون هاوس"],
            },
            {
                "name": "أراضي ومزارع",
                "leaves": ["أراضي سكنية", "أراضي تجارية", "مزارع واستراحات", "مخططات جديدة"],
            },
        ],
    },
    {
        "name": "ركن الإلكترونيات",
        "subs": [
            {
                "name": "جوالات وتابلت",
                "leaves": ["آيفون 15", "سامسونج S24", "آيباد برو", "هواوي", "شاومي", "جوالات مستعملة", "إكسسوارات جوال"],
            },
            {
                "name": "كمبيوتر ولابتوب",
                "leaves": ["ماك بوك", "لابتوب جيمينج", "تجميعات PC", "شاشات 4K", "طابعات", "لوحات مفاتيح ميكانيكية"],
            },
            {
                "name": "ألعاب فيديو",
                "leaves": ["بلايستيشن 5", "إكس بوكس", "نينتندو سويتش", "حسابات ألعاب", "كروت شحن"],
            },
        ],
    },
    {
        "name": "ركن الأثاث والديكورات",
        "subs": [
            {
                "name": "غرف الجلوس",
                "leaves": ["كنب مودرن", "طاولات قهوة", "سجاد إيراني", "ستائر", "ورق حائط", "إضاءات سقف", "مكتبات تلفزيون"],
            },
            {
                "name": "غرف النوم",
                "leaves": ["أسرة مزدوجة", "خزائن ملابس", "مفارش", "مراتب طبية", "تسريحات", "غرف أطفال"],
            },
            {
                "name": "المطابخ",
                "leaves": ["خزائن مطبخ", "أدوات مائدة", "أجهزة طبخ", "طاولات طعام", "ميكرويف"],
            },
        ],
    },
    {
        "name": "ركن الوظائف",
        "subs": [
            {
                "name": "وظائف إدارية",
                "leaves": ["سكرتارية", "إدارة مشاريع", "موارد بشرية", "خدمة عملاء", "إدخال بيانات"],
            },
            {
                "name": "وظائف تقنية",
                "leaves": ["مطور ويب", "مطور تطبيقات", "دعم فني", "أمن معلومات", "تحليل بيانات"],
            },
        ],
    },
    {
        "name": "ركن الخدمات",
        "subs": [
            {
                "name": "خدمات منزلية",
                "leaves": ["سباكة", "كهرباء", "تنظيف منازل", "مكافحة حشرات", "نقل عفش"],
            },
            {
                "name": "خدمات مهنية",
                "leaves": ["تصميم جرافيك", "تصوير", "تسويق رقمي", "كتابة محتوى", "استشارات"],
            },
        ],
    },
    {
        "name": "ركن الحيوانات",
        "subs": [
            {
                "name": "حيوانات أليفة",
                "leaves": ["قطط", "كلاب", "طيور", "أسماك", "أرانب"],
            },
            {
                "name": "مستلزمات الحيوانات",
                "leaves": ["أطعمة", "أقفاص", "ألعاب", "رعاية صحية", "إكسسوارات"],
            },
        ],
    },
    {
        "name": "ركن الموضة والجمال",
        "subs": [
            {
                "name": "ملابس",
                "leaves": ["ملابس رجالية", "ملابس نسائية", "ملابس أطفال", "ملابس رياضية"],
            },
            {
                "name": "تجميل وعناية",
                "leaves": ["مكياج", "عطور", "عناية بالبشرة", "عناية بالشعر", "أدوات تجميل"],
            },
        ],
    },
    {
        "name": "ركن السفر والسياحة",
        "subs": [
            {
                "name": "رحلات وسياحة",
                "leaves": ["رحلات داخلية", "رحلات خارجية", "عروض سياحية", "حج وعمرة"],
            },
            {
                "name": "حجوزات",
                "leaves": ["تذاكر طيران", "حجوزات فنادق", "تأجير سيارات", "تأمين سفر"],
            },
        ],
    },
    {
        "name": "ركن التعليم والتدريب",
        "subs": [
            {
                "name": "دورات تعليمية",
                "leaves": ["دورات أونلاين", "لغات", "برمجة", "تصميم", "إدارة أعمال"],
            },
            {
                "name": "خدمات تعليمية",
                "leaves": ["دروس خصوصية", "حل واجبات", "أبحاث جامعية", "استشارات تعليمية"],
            },
        ],
    },
    {
        "name": "ركن الرياضة والهوايات",
        "subs": [
            {
                "name": "معدات رياضية",
                "leaves": ["أجهزة رياضية", "أدوات كمال أجسام", "ملابس رياضية", "مكملات غذائية"],
            },
            {
                "name": "هوايات",
                "leaves": ["تصوير", "رسم", "موسيقى", "ألعاب هواة", "تخييم"],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the initial category tree (root → sub → leaf)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete ALL existing categories before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Category.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing categories."))

        roots = created_count = 0

        for root_data in CATEGORIES:
            root, created = Category.objects.get_or_create(
                name=root_data["name"],
                defaults={"parent": None},
            )
            if created:
                roots += 1

            for sub_data in root_data["subs"]:
                sub, created = Category.objects.get_or_create(
                    name=sub_data["name"],
                    defaults={"parent": root},
                )
                if created:
                    created_count += 1

                for leaf_name in sub_data["leaves"]:
                    _, created = Category.objects.get_or_create(
                        name=leaf_name,
                        defaults={"parent": sub},
                    )
                    if created:
                        created_count += 1

        total_created = roots + created_count
        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {total_created} categories "
            f"({roots} roots, {created_count} subs/leaves)."
        ))
