from django.db import migrations


def forwards(apps, schema_editor):
    Province = apps.get_model('reeftrack_app', 'Province')
    Municipality = apps.get_model('reeftrack_app', 'Municipality')
    province, _ = Province.objects.get_or_create(name='Sarangani')
    Municipality.objects.filter(province__isnull=True).update(province=province)


def backwards(apps, schema_editor):
    Municipality = apps.get_model('reeftrack_app', 'Municipality')
    Municipality.objects.all().update(province=None)


class Migration(migrations.Migration):

    dependencies = [
        ('reeftrack_app', '0024_province_alter_municipality_name_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
