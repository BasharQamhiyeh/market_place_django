from django.core.management.base import BaseCommand
from django.db import transaction

from marketplace.models import PrivacyPolicyPage, PrivacyPolicySection


PAGE = {
    "title_ar": "سياسة الخصوصية",
    "subtitle_ar": "نوضح هنا كيف نجمع بياناتك ونستخدمها ونحميها داخل منصة ركن.",
    "sidebar_note_ar": "بياناتك في أمان. نلتزم بسرية معلوماتك ولن نشاركها مع أي طرف ثالث دون موافقتك.",
    "cta_title_ar": "هل لديك استفسار؟",
    "cta_subtitle_ar": "إذا كان لديك أي سؤال حول سياسة الخصوصية أو كيفية التعامل مع بياناتك، فريق الدعم لدينا جاهز لمساعدتك.",
    "cta_button_ar": "تواصل مع الدعم الفني",
    "cta_url": "#",
}

SECTIONS = [
    {
        "order": 1,
        "anchor_key": "introduction",
        "icon": "shield",
        "title_ar": "مقدمة",
        "body_ar": (
            "تُعدّ هذه السياسة جزءاً أساسياً من علاقتنا معك كمستخدم لمنصة ركن. "
            "نحن ملتزمون بحماية خصوصيتك وضمان أمان بياناتك الشخصية وفق أعلى المعايير.\n\n"
            "باستخدامك للمنصة، فإنك توافق على ممارسات جمع البيانات واستخدامها المبيّنة في هذه الوثيقة. "
            "يُرجى قراءة هذه السياسة بعناية قبل البدء باستخدام الموقع."
        ),
    },
    {
        "order": 2,
        "anchor_key": "collection",
        "icon": "database",
        "title_ar": "البيانات التي نجمعها",
        "body_ar": (
            "نجمع فقط المعلومات الضرورية لتشغيل المنصة وتحسين تجربتك:\n\n"
            "• بيانات الحساب: رقم الجوال، الاسم، وصورة الملف الشخصي (اختيارية).\n"
            "• بيانات الإعلانات والطلبات: العنوان، الوصف، الصور، والموقع الجغرافي.\n"
            "• بيانات الاستخدام: الصفحات التي تزورها وطريقة تفاعلك مع المنصة.\n"
            "• بيانات التواصل: الرسائل التي ترسلها عبر نماذج الدعم."
        ),
    },
    {
        "order": 3,
        "anchor_key": "usage",
        "icon": "settings",
        "title_ar": "كيف نستخدم بياناتك",
        "body_ar": (
            "نستخدم البيانات المجموعة للأغراض التالية حصراً:\n\n"
            "• تشغيل الخدمات: عرض إعلاناتك، تمكين التواصل بين المستخدمين، وإدارة حسابك.\n"
            "• تحسين المنصة: تحليل طريقة الاستخدام لتطوير الميزات وتحسين الأداء.\n"
            "• الأمان: الكشف عن الأنشطة المشبوهة وحماية مستخدمي المنصة.\n"
            "• الدعم الفني: الرد على استفساراتك وحل المشكلات التقنية."
        ),
    },
    {
        "order": 4,
        "anchor_key": "sharing",
        "icon": "share-2",
        "title_ar": "مشاركة البيانات",
        "body_ar": (
            "لا نبيع بياناتك الشخصية ولا نشاركها مع أطراف ثالثة لأغراض تجارية. "
            "قد نشارك معلوماتك في الحالات التالية فقط:\n\n"
            "• مزودو الخدمات: شركاء تقنيون موثوقون يساعدون في تشغيل المنصة (مثل خدمات الرسائل النصية)، "
            "وهم ملزمون بالحفاظ على سرية بياناتك.\n"
            "• المتطلبات القانونية: عند وجود أمر قضائي أو طلب رسمي من جهة حكومية مختصة.\n"
            "• حماية الحقوق: عند الضرورة لحماية حقوق ركن أو مستخدميها من الانتهاكات."
        ),
    },
    {
        "order": 5,
        "anchor_key": "security",
        "icon": "lock",
        "title_ar": "حماية بياناتك",
        "body_ar": (
            "نتخذ إجراءات أمنية وتقنية صارمة لحماية بياناتك:\n\n"
            "• تشفير البيانات أثناء النقل باستخدام بروتوكول HTTPS.\n"
            "• تخزين كلمات المرور بصورة مشفرة ولا يمكن الاطلاع عليها.\n"
            "• تقييد وصول فريق العمل الداخلي للبيانات الشخصية على أساس الحاجة فقط.\n"
            "• مراجعة دورية لأنظمة الأمان لضمان حمايتك من التهديدات المستجدة."
        ),
    },
    {
        "order": 6,
        "anchor_key": "rights",
        "icon": "user-check",
        "title_ar": "حقوقك",
        "body_ar": (
            "باعتبارك مستخدماً لمنصة ركن، تتمتع بالحقوق التالية:\n\n"
            "• الاطلاع: طلب نسخة من بياناتك الشخصية المحفوظة لدينا.\n"
            "• التصحيح: تعديل أي معلومات غير دقيقة من خلال إعدادات حسابك.\n"
            "• الحذف: طلب حذف حسابك وبياناتك المرتبطة به نهائياً.\n"
            "• الاعتراض: الاعتراض على أي استخدام لبياناتك لا تراه مناسباً.\n\n"
            "لممارسة أي من هذه الحقوق، يُرجى التواصل معنا عبر صفحة الدعم الفني."
        ),
    },
    {
        "order": 7,
        "anchor_key": "updates",
        "icon": "refresh-cw",
        "title_ar": "تحديثات السياسة",
        "body_ar": (
            "قد نُحدّث سياسة الخصوصية هذه من وقت لآخر لتعكس التغييرات في خدماتنا أو المتطلبات القانونية. "
            "سيتم إخطارك بأي تغييرات جوهرية عبر إشعار واضح على المنصة.\n\n"
            "نوصي بمراجعة هذه الصفحة بشكل دوري. استمرارك في استخدام المنصة بعد نشر التحديثات "
            "يُعدّ قبولاً ضمنياً للسياسة المحدّثة."
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
