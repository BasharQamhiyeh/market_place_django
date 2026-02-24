from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0036_remove_bilingual_attribute_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # These run against the actual database (safe/conditional)
            database_operations=[
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_city' AND column_name='name'
                        ) THEN
                            ALTER TABLE marketplace_city ADD COLUMN name VARCHAR(150) NOT NULL DEFAULT '';
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_city' AND column_name='name_ar'
                        ) THEN
                            UPDATE marketplace_city SET name = name_ar WHERE name = '' OR name IS NULL;
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_city' AND column_name='name_ar'
                        ) THEN
                            ALTER TABLE marketplace_city DROP COLUMN name_ar;
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_city' AND column_name='name_en'
                        ) THEN
                            ALTER TABLE marketplace_city DROP COLUMN name_en;
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_indexes
                            WHERE tablename='marketplace_city' AND indexname='marketplace_city_name_unique'
                        ) THEN
                            ALTER TABLE marketplace_city ADD CONSTRAINT marketplace_city_name_unique UNIQUE (name);
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            # These update Django's migration state only (no DB operations)
            state_operations=[
                migrations.AddField(
                    model_name="city",
                    name="name",
                    field=models.CharField(max_length=150, default=""),
                    preserve_default=False,
                ),
                migrations.AlterField(
                    model_name="city",
                    name="name",
                    field=models.CharField(max_length=150, unique=True),
                ),
            ],
        ),
    ]