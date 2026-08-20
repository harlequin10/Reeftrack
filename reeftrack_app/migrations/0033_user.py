from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reeftrack_app', '0032_update_site_domain'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE auth_user DROP COLUMN IF EXISTS username CASCADE;",
            reverse_sql="ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS username VARCHAR(150) DEFAULT '';",
        ),
    ]
