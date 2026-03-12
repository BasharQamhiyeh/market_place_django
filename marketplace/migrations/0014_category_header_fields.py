from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0013_conversation_report_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="show_in_header",
            field=models.BooleanField(
                default=False,
                help_text="Prioritise this category in the header navigation.",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="header_question",
            field=models.CharField(
                blank=True,
                default="هل تريد نشر إعلان؟",
                help_text="Promo question shown in the mega-menu (level-1 categories only).",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="header_action",
            field=models.CharField(
                blank=True,
                default="انشر إعلانك الآن مجاناً",
                help_text="Promo action text shown in the mega-menu (level-1 categories only).",
                max_length=255,
            ),
        ),
    ]
