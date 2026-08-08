import os

from django.db import migrations


def set_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    host = None
    for h in os.getenv('ALLOWED_HOSTS', 'localhost').split(','):
        h = h.strip()
        if h and not h.startswith('.'):
            host = h
            break
    if not host:
        host = 'localhost'
    Site.objects.filter(id=1).update(name=host, domain=host)


class Migration(migrations.Migration):

    dependencies = [
        ('reeftrack_app', '0031_userprofile_profile_completed'),
    ]

    operations = [
        migrations.RunPython(set_site_domain, migrations.RunPython.noop),
    ]
