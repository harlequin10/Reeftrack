from django.db import migrations


def normalize_species_case(apps, schema_editor):
    """Normalize all species sub_category and major_category to UPPER CASE."""
    Species = apps.get_model('reeftrack_app', 'Species')
    for sp in Species.objects.all():
        sp.sub_category = sp.sub_category.strip().upper()
        sp.major_category = sp.major_category.strip().upper()
        sp.save(update_fields=['sub_category', 'major_category'])


def reverse_func(apps, schema_editor):
    pass  # No reverse needed


class Migration(migrations.Migration):

    dependencies = [
        ('reeftrack_app', '0019_alter_contributor_middle_initial_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_species_case, reverse_func),
    ]
