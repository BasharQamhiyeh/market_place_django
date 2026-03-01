from django.db import migrations


class Migration(migrations.Migration):
    """Install the pg_trgm PostgreSQL extension for trigram similarity search."""

    dependencies = [
        ("marketplace", "0009_sitesettings"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql="DROP EXTENSION IF EXISTS pg_trgm;",
        ),
    ]
