from django.core.management.base import BaseCommand
from django.db import transaction

from marketplace.models import PrivacyPolicyPage, PrivacyPolicySection


PAGE = {
    "title_ar": "سياسة الخصوصية",
    "subtitle_ar": "خصوصيتك هي أمانتنا. نحن نلتزم بحماية بياناتك الشخصية تماماً كما نلتزم بجودة خدماتنا.",
    "sidebar_note_ar": "ملتزمون بأفضل ممارسات حماية البيانات والخصوصية.",
    "cta_title_ar": "هل لديك استفسار حول خصوصيتك؟",
    "cta_subtitle_ar": "فريقنا القانوني والتقني جاهز لتوضيح أي نقطة تتعلق بكيفية تعاملنا مع بياناتك.",
    "cta_button_ar": "تواصل مع الدعم الفني",
    "cta_url": "#",
}

SECTIONS = [
    {
        "order": 1,
        "anchor_key": "intro",
        "icon": "info",
        "title_ar": "مقدمة عامة",
        "body_ar": (
            "توضح سياسة الخصوصية هذه الأسس التي يقوم عليها فريق ركن بجمع واستخدام وحماية "
            "المعلومات الشخصية الخاصة بك عند استخدامك للمنصة. نحن ندرك تماماً أهمية بياناتك، "
            "لذا نستخدم أفضل المعايير التقنية لضمان بقاء معلوماتك آمنة وسرية."
        ),
    },
    {
        "order": 2,
        "anchor_key": "data-collection",
        "icon": "database",
        "title_ar": "المعلومات التي نقوم بجمعها",
        "body_ar": (
            "نقوم بجمع نوعين من المعلومات لضمان عمل المنصة بكفاءة:\n"
            "• بيانات الحساب: الاسم، رقم الهاتف، والبريد الإلكتروني الذي تزودنا به عند التسجيل.\n"
            "• بيانات النشاط: سجل الإعلانات، عمليات البحث، والمواقع الجغرافية التقريبية "
            "لتحسين ظهور النتائج المناسبة لك."
        ),
    },
    {
        "order": 3,
        "anchor_key": "data-usage",
        "icon": "settings-2",
        "title_ar": "كيفية استخدام المعلومات",
        "body_ar": (
            "نستخدم معلوماتك الشخصية فقط لأغراض واضحة: إدارة حسابك في ركن، تمكينك من إضافة "
            "الإعلانات والطلبات، تسهيل التواصل بينك وبين المستخدمين الآخرين عبر الدردشة، وإرسال "
            "تنبيهات هامة بخصوص إعلاناتك أو تحديثات المنصة."
        ),
    },
    {
        "order": 4,
        "anchor_key": "protection",
        "icon": "lock",
        "title_ar": "حماية وأمان البيانات",
        "body_ar": (
            "نحن نطبق إجراءات أمنية معقدة وتقنيات تشفير متطورة لحماية بياناتك من أي وصول غير "
            "مصرح به. خوادمنا محمية بجدران حماية برمجية، ونقوم بمراجعة ممارسات الأمان لدينا بشكل دوري."
        ),
    },
    {
        "order": 5,
        "anchor_key": "sharing",
        "icon": "share-2",
        "title_ar": "مشاركة المعلومات",
        "body_ar": (
            "في ركن، لا نقوم ببيع أو تأجير أو مشاركة بياناتك الشخصية مع أطراف خارجية لأغراض "
            "تسويقية. نحن نفصح عن المعلومات فقط في حالات محدودة جداً: عند وجود طلب قانوني رسمي، "
            "أو لحماية حقوق وسلامة مستخدمينا، أو مع مزودي الخدمات الذين يساعدوننا في تشغيل "
            "المنصة (تحت اتفاقيات سرية صارمة)."
        ),
    },
    {
        "order": 6,
        "anchor_key": "rights",
        "icon": "user-check",
        "title_ar": "حقوق المستخدم",
        "body_ar": (
            "بصفتك مستخدماً في ركن، فلك الحق في الوصول إلى معلوماتك الشخصية في أي وقت وتعديلها "
            "أو تحديثها. كما يمكنك طلب حذف حسابك وبياناتك بالكامل من خلال إعدادات الحساب أو "
            "التواصل المباشر مع فريق الدعم الفني لدينا."
        ),
    },
]


class Command(BaseCommand):
    help = "Seed Privacy Policy page + sections from the UI mockup."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Deactivate existing active page and create a fresh one.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["replace"]:
            PrivacyPolicyPage.objects.update(is_active=False)

        # Skip if an active page already exists (idempotent by default)
        if not options["replace"] and PrivacyPolicyPage.objects.filter(is_active=True).exists():
            self.stdout.write(self.style.WARNING(
                "Active PrivacyPolicyPage already exists. Use --replace to overwrite."
            ))
            return

        page = PrivacyPolicyPage.objects.create(
            title_ar=PAGE["title_ar"],
            subtitle_ar=PAGE["subtitle_ar"],
            sidebar_note_ar=PAGE["sidebar_note_ar"],
            cta_title_ar=PAGE["cta_title_ar"],
            cta_subtitle_ar=PAGE["cta_subtitle_ar"],
            cta_button_ar=PAGE["cta_button_ar"],
            cta_url=PAGE["cta_url"],
            is_active=True,
        )

        PrivacyPolicySection.objects.bulk_create([
            PrivacyPolicySection(
                page=page,
                order=s["order"],
                anchor_key=s["anchor_key"],
                icon=s["icon"],
                title_ar=s["title_ar"],
                body_ar=s["body_ar"],
                is_active=True,
            )
            for s in SECTIONS
        ])

        self.stdout.write(self.style.SUCCESS(
            f"Created PrivacyPolicyPage id={page.id} with {len(SECTIONS)} sections."
        ))
