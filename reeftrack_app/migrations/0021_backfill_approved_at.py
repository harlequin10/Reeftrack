from django.db import migrations


def backfill_approved_at(apps, schema_editor):
    Assessment = apps.get_model('reeftrack_app', 'Assessment')
    for a in Assessment.objects.filter(status='approved', approved_at__isnull=True):
        a.approved_at = a.updated_at or a.created_at
        a.save(update_fields=['approved_at'])


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('reeftrack_app', '0020_normalize_species_case'),
    ]

    operations = [
        migrations.RunPython(backfill_approved_at, reverse_func),
    ]
