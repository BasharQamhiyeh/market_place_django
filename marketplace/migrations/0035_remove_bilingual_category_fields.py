from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0034_issuesreport_action_taken_issuesreport_actioned_at_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_category' AND column_name='name'
                        ) THEN
                            ALTER TABLE marketplace_category ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT '';
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_category' AND column_name='subtitle'
                        ) THEN
                            ALTER TABLE marketplace_category ADD COLUMN subtitle VARCHAR(255) NULL;
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
                            WHERE table_name='marketplace_category' AND column_name='name_ar'
                        ) THEN
                            UPDATE marketplace_category 
                            SET name = COALESCE(NULLIF(name_ar, ''), NULLIF(name_en, ''), '')
                            WHERE name = '';
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
                            WHERE table_name='marketplace_category' AND column_name='subtitle_ar'
                        ) THEN
                            UPDATE marketplace_category SET subtitle = NULLIF(subtitle_ar, '');
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_category' AND column_name='name_ar') THEN
                            ALTER TABLE marketplace_category DROP COLUMN name_ar; END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_category' AND column_name='name_en') THEN
                            ALTER TABLE marketplace_category DROP COLUMN name_en; END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_category' AND column_name='subtitle_ar') THEN
                            ALTER TABLE marketplace_category DROP COLUMN subtitle_ar; END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_category' AND column_name='subtitle_en') THEN
                            ALTER TABLE marketplace_category DROP COLUMN subtitle_en; END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_category' AND column_name='child_label') THEN
                            ALTER TABLE marketplace_category DROP COLUMN child_label; END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_category' AND column_name='icon') THEN
                            ALTER TABLE marketplace_category DROP COLUMN icon; END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_category' AND column_name='color') THEN
                            ALTER TABLE marketplace_category DROP COLUMN color; END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_indexes
                            WHERE tablename='marketplace_category' AND indexname='marketplace_category_name_key'
                        ) THEN
                            ALTER TABLE marketplace_category ADD CONSTRAINT marketplace_category_name_key UNIQUE (name);
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="category",
                    name="name",
                    field=models.CharField(max_length=255, default=""),
                    preserve_default=False,
                ),
                migrations.AlterField(
                    model_name="category",
                    name="name",
                    field=models.CharField(max_length=255, unique=True),
                ),
                migrations.AddField(
                    model_name="category",
                    name="subtitle",
                    field=models.CharField(max_length=255, blank=True, null=True),
                ),
            ],
        ),
    ]