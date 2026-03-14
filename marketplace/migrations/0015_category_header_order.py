from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0014_category_header_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="category",
            name="show_in_header",
        ),
        migrations.AddField(
            model_name="category",
            name="header_order",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                help_text=(
                    "Position in the header navigation (1–6 for top-level, 1–3 for sub-levels). "
                    "Leave empty to hide from the header. Each number may only be used once per sibling group."
                ),
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                condition=models.Q(parent__isnull=True) & models.Q(header_order__isnull=False),
                fields=["header_order"],
                name="unique_header_order_top_level",
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                condition=models.Q(parent__isnull=False) & models.Q(header_order__isnull=False),
                fields=["parent", "header_order"],
                name="unique_header_order_per_parent",
            ),
        ),
    ]
