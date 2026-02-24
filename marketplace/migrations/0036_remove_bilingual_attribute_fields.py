from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0035_remove_bilingual_category_fields'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Attribute: add name
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_attribute' AND column_name='name'
                        ) THEN
                            ALTER TABLE marketplace_attribute ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT '';
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # AttributeOption: add value
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_attributeoption' AND column_name='value'
                        ) THEN
                            ALTER TABLE marketplace_attributeoption ADD COLUMN value VARCHAR(255) NOT NULL DEFAULT '';
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # Copy name_ar -> name
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_attribute' AND column_name='name_ar'
                        ) THEN
                            UPDATE marketplace_attribute
                            SET name = COALESCE(NULLIF(name_ar, ''), NULLIF(name_en, ''), '')
                            WHERE name = '';
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # Copy value_ar -> value
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='marketplace_attributeoption' AND column_name='value_ar'
                        ) THEN
                            UPDATE marketplace_attributeoption
                            SET value = COALESCE(NULLIF(value_ar, ''), NULLIF(value_en, ''), '')
                            WHERE value = '';
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # Drop old columns
                migrations.RunSQL(
                    """
                    DO $$ BEGIN
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_attribute' AND column_name='name_ar') THEN
                            ALTER TABLE marketplace_attribute DROP COLUMN name_ar; END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_attribute' AND column_name='name_en') THEN
                            ALTER TABLE marketplace_attribute DROP COLUMN name_en; END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_attributeoption' AND column_name='value_ar') THEN
                            ALTER TABLE marketplace_attributeoption DROP COLUMN value_ar; END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='marketplace_attributeoption' AND column_name='value_en') THEN
                            ALTER TABLE marketplace_attributeoption DROP COLUMN value_en; END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="attribute",
                    name="name",
                    field=models.CharField(max_length=255, default=""),
                    preserve_default=False,
                ),
                migrations.AlterField(
                    model_name="attribute",
                    name="name",
                    field=models.CharField(max_length=255),
                ),
                migrations.AddField(
                    model_name="attributeoption",
                    name="value",
                    field=models.CharField(max_length=255, default=""),
                    preserve_default=False,
                ),
                migrations.AlterField(
                    model_name="attributeoption",
                    name="value",
                    field=models.CharField(max_length=255),
                ),
            ],
        ),
    ]