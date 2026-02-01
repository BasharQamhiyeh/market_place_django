from django.core.management.base import BaseCommand
from django.db import transaction

# ⚠️ عدّل أسماء الموديلات/الحقول حسب مشروعك إذا كانت مختلفة
from marketplace.models import PrivacyPolicyPage, PrivacyPolicySection


PAGE = {
    "title_ar": "سياسة الخصوصية",
    "subtitle_ar": "ركن: حيث تلتقي الثقة بالسهولة",
}

SECTIONS = [
    {
        "order": 1,
        "heading_ar": "تسوّق في ركن بحرية تامة، بلا قيود.",
        "body_ar": (
            'تجاوزنا قيود التسجيل التقليدية. في ركن، يمكنك تصفح آلاف العقارات، السيارات، '
            'والأجهزة الإلكترونية فوراً. ابحث عما تريد، تواصل بجدية، وأنجز صفقاتك بكل سلاسة.'
        ),
    },
    {
        "order": 2,
        "heading_ar": "وداعاً للتعقيد.. أهلاً بـ عصر جديد",
        "body_ar": 'صممنا "ركن" لنحل المشاكل التي لطالما أزعجتك في المواقع الأخرى',
    },
    {
        "order": 3,
        "heading_ar": "المواقع التقليدية — تجربة مليئة بالعقبات",
        "body_ar": (
            "• إجبارك على إنشاء حساب قبل مشاهدة الصور والأسعار.\n"
            "• إعلانات منبثقة (Pop-ups) تعيق تصفحك وتشتت انتباهك.\n"
            "• سياسات معقدة لنشر إعلانك تستهلك الكثير من وقتك.\n"
            "• واجهات قديمة وصعبة الاستخدام على الهواتف الذكية.\n"
            "• صعوبة الوصول المباشر لبيانات التواصل مع البائع.\n\n"
            "تجربة محبطة للمستخدم.."
        ),
    },
    {
        "order": 4,
        "heading_ar": "منصة ركن — بساطة، سرعة، وخصوصية",
        "body_ar": (
            "• تصفح كامل وحرية تامة دون الحاجة لأي تسجيل.\n"
            "• واجهة عصرية نظيفة تركز فقط على ما يهمك.\n"
            "• انشر إعلانك في 30 ثانية فقط بخطوات ذكية.\n"
            "• تصميم مستجيب يمنحك تجربة تطبيق على المتصفح.\n"
            "• تواصل عبر الواتساب أو الاتصال بضغطة واحدة."
        ),
    },
    {
        "order": 5,
        "heading_ar": "كيف يعمل ركن؟",
        "body_ar": (
            "01 — حرية التصفح (خصوصيتك أولاً)\n"
            "افتح الموقع وشاهد كل التفاصيل، الصور، والأسعار فوراً. لا توجد عوائق أو نوافذ إجبارية "
            "تطلب بياناتك الشخصية قبل أن تقرر ما تريد.\n\n"
            "02 — تواصل مباشر (بكل سهولة)\n"
            "عندما تجد طلبك وتكون جاهزاً للتفاوض أو نشر إعلانك، يمكنك إنشاء حسابك في لحظات لتتمكن "
            "من مراسلة المعلنين وإتمام صفقاتك بأمان.\n\n"
            "03 — لم تجد طلبك (لا تقلق)\n"
            "أضف طلبك بالتفصيل وانتظر عروض المعلنين\n\n"
            "04 — نمو أعمالك (حلول التجار)\n"
            "هل أنت تاجر أو صاحب مهنة؟\n"
            'أنشئ "متجراً رقمياً" متكاملاً يجمع كافة عروضك تحت سقف واحد، مما يسهل على العملاء الوصول '
            "إليك وبناء ثقة مستدامة بعلامتك التجارية."
        ),
    },
    {
        "order": 6,
        "heading_ar": "ابدأ رحلة النجاح مع ركن",
        "body_ar": (
            "سواء كنت مشترياً يبحث عن الأفضل، أو تاجراً يرغب في الانتشار، "
            '"ركن" هو المكان المناسب لك.'
        ),
    },
]


class Command(BaseCommand):
    help = "Seed Privacy Policy page + sections (exact extracted text from provided mockup)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Deactivate old pages and create a new active page.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        replace = options["replace"]

        if replace:
            PrivacyPolicyPage.objects.update(is_active=False)

        page = PrivacyPolicyPage.objects.create(
            title_ar=PAGE["title_ar"],
            subtitle_ar=PAGE["subtitle_ar"],
            is_active=True,
        )

        PrivacyPolicySection.objects.bulk_create([
            PrivacyPolicySection(
                page=page,
                order=s["order"],
                heading_ar=s["heading_ar"],
                body_ar=s["body_ar"],
                is_active=True,
            )
            for s in SECTIONS
        ])

        self.stdout.write(self.style.SUCCESS(
            f"Created PrivacyPolicyPage id={page.id} with {len(SECTIONS)} sections."
        ))
