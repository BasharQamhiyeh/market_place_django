from django.core.management.base import BaseCommand
from django.db import transaction

from marketplace.models import TermsPage, TermsSection


PAGE = {
    "title_ar": "شروط الاستخدام",
    "subtitle_ar": "ميثاقنا المشترك لضمان تجربة آمنة وموثوقة لكافة مستخدمي منصة ركن.",
    "sidebar_note_ar": "باستخدامك للمنصة، أنت توافق ضمنياً على كافة البنود المذكورة هنا.",
}

SECTIONS = [
    {
        "order": 1,
        "anchor_key": "acceptance",
        "icon": "check-circle",
        "title_ar": "القبول بالشروط",
        "body_ar": (
            "باستخدامك لمنصة ركن — سواء بالتصفح أو التسجيل أو نشر الإعلانات — فإنك توافق "
            "صراحةً على الالتزام بجميع البنود والشروط الواردة في هذه الوثيقة.\n\n"
            "إذا كنت لا توافق على أي من هذه الشروط، يُرجى التوقف عن استخدام المنصة "
            "والتواصل معنا لأي استفسار."
        ),
        "warning_ar": "",
    },
    {
        "order": 2,
        "anchor_key": "account",
        "icon": "user-check",
        "title_ar": "استخدام الحساب",
        "body_ar": (
            "• يُسمح بإنشاء حساب واحد فقط لكل مستخدم، مرتبط برقم موبايل حقيقي وفعّال.\n"
            "• أنت مسؤول مسؤولية كاملة عن الحفاظ على سرية بيانات تسجيل الدخول الخاصة بك.\n"
            "• يجب أن تكون المعلومات المدخلة في ملفك الشخصي صحيحة ودقيقة.\n"
            "• يحق لنا تعليق أو إلغاء أي حساب يُشتبه في انتهاكه لهذه الشروط أو الإضرار "
            "بمستخدمين آخرين."
        ),
        "warning_ar": "",
    },
    {
        "order": 3,
        "anchor_key": "content",
        "icon": "megaphone",
        "title_ar": "نشر الإعلانات والطلبات",
        "body_ar": (
            "• يجب أن تكون الإعلانات والطلبات المنشورة صادقة، دقيقة، وغير مضللة.\n"
            "• يُمنع نشر الإعلان ذاته أكثر من مرة واحدة في نفس الوقت أو في أقسام غير ذات صلة.\n"
            "• تخضع الإعلانات للمراجعة قبل النشر، وقد يُرفض أي إعلان لا يستوفي معايير الجودة.\n"
            "• يمكنك تعديل أو حذف إعلانك في أي وقت من خلال لوحة تحكم حسابك.\n"
            "• يبقى الإعلان نشطاً حتى تقوم بحذفه أو انتهاء صلاحيته، مع إمكانية إعادة رفعه "
            "كل 7 أيام ليظهر في المقدمة."
        ),
        "warning_ar": "",
    },
    {
        "order": 4,
        "anchor_key": "prohibited",
        "icon": "ban",
        "title_ar": "المحتوى المحظور",
        "body_ar": (
            "يُحظر تماماً نشر أي محتوى يندرج ضمن الفئات التالية:\n\n"
            "• المواد المخالفة للقانون الأردني أو الآداب العامة.\n"
            "• الأسلحة، المخدرات، المواد الخطرة أو المقلّدة.\n"
            "• الإعلانات الاحتيالية أو المضللة لأغراض النصب والاحتيال.\n"
            "• أي محتوى يحتوي على تحرش، تمييز، أو انتهاك لخصوصية الأفراد.\n"
            "• منتجات أو خدمات مسروقة أو غير مرخصة."
        ),
        "warning_ar": (
            "الانتهاك يؤدي إلى تعليق الحساب فوراً، وقد يُحال الأمر للجهات القانونية المختصة."
        ),
    },
    {
        "order": 5,
        "anchor_key": "liability",
        "icon": "shield-off",
        "title_ar": "إخلاء المسؤولية",
        "body_ar": (
            "ركن منصة وسيطة تُتيح للمستخدمين عرض الإعلانات والطلبات والتواصل فيما بينهم. "
            "لذلك:\n\n"
            "• لا تتحمل ركن أي مسؤولية عن الاتفاقات أو المعاملات التي تتم بين المستخدمين "
            "خارج المنصة.\n"
            "• لا تضمن ركن جودة المنتجات أو الخدمات المعروضة أو صحة بيانات المعلنين.\n"
            "• عمليات الشراء والبيع والتفاوض تتم على مسؤولية الأطراف المعنية بالكامل."
        ),
        "warning_ar": (
            "ننصح بشدة بعدم تحويل أي مبالغ مالية مسبقة دون التحقق من هوية الطرف الآخر "
            "ومعاينة المنتج أو الخدمة."
        ),
    },
    {
        "order": 6,
        "anchor_key": "privacy",
        "icon": "lock",
        "title_ar": "الخصوصية وحماية البيانات",
        "body_ar": (
            "نُولي خصوصيتك أهمية قصوى. يتم جمع البيانات الشخصية الضرورية فقط لتشغيل "
            "المنصة وتحسين تجربتك، ولن تُشارَك مع أطراف ثالثة دون موافقتك الصريحة، "
            "إلا في الحالات التي يُوجبها القانون.\n\n"
            "لمزيد من التفاصيل حول كيفية جمع البيانات واستخدامها وحمايتها، يُرجى الاطلاع "
            "على سياسة الخصوصية الخاصة بنا."
        ),
        "warning_ar": "",
    },
    {
        "order": 7,
        "anchor_key": "changes",
        "icon": "refresh-cw",
        "title_ar": "التعديلات على الشروط",
        "body_ar": (
            "تحتفظ ركن بالحق في تعديل هذه الشروط في أي وقت. سيتم إخطار المستخدمين "
            "بأي تغييرات جوهرية عبر الموقع أو البريد الإلكتروني.\n\n"
            "استمرارك في استخدام المنصة بعد نشر التعديلات يُعدّ قبولاً ضمنياً منك للشروط "
            "الجديدة. يُنصح بمراجعة هذه الصفحة بشكل دوري للاطلاع على أحدث النسخ."
        ),
        "warning_ar": "",
    },
]


class Command(BaseCommand):
    help = "Seed Terms of Use page + sections from the UI mockup."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Deactivate existing active page and create a fresh one.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["replace"]:
            TermsPage.objects.update(is_active=False)

        # Skip if an active page already exists (idempotent by default)
        if not options["replace"] and TermsPage.objects.filter(is_active=True).exists():
            self.stdout.write(self.style.WARNING(
                "Active TermsPage already exists. Use --replace to overwrite."
            ))
            return

        page = TermsPage.objects.create(
            title_ar=PAGE["title_ar"],
            subtitle_ar=PAGE["subtitle_ar"],
            sidebar_note_ar=PAGE["sidebar_note_ar"],
            is_active=True,
        )

        TermsSection.objects.bulk_create([
            TermsSection(
                page=page,
                order=s["order"],
                anchor_key=s["anchor_key"],
                icon=s["icon"],
                title_ar=s["title_ar"],
                body_ar=s["body_ar"],
                warning_ar=s["warning_ar"],
                is_active=True,
            )
            for s in SECTIONS
        ])

        self.stdout.write(self.style.SUCCESS(
            f"Created TermsPage id={page.id} with {len(SECTIONS)} sections."
        ))
