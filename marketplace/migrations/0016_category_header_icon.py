from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0015_category_header_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="header_icon",
            field=models.CharField(
                blank=True,
                default="megaphone",
                max_length=64,
                help_text="Lucide icon name shown in the mega-menu promo card (e.g. megaphone, car, home, tag).",
            ),
        ),
    ]
