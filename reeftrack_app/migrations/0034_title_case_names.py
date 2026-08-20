from django.db import migrations


def title_case_names(apps, schema_editor):
    User = apps.get_model('reeftrack_app', 'User')
    for user in User.objects.all():
        changed = False
        if user.first_name:
            new_name = user.first_name.strip().title()
            if new_name != user.first_name:
                user.first_name = new_name
                changed = True
        if user.last_name:
            new_name = user.last_name.strip().title()
            if new_name != user.last_name:
                user.last_name = new_name
                changed = True
        if changed:
            user.save(update_fields=['first_name', 'last_name'])


class Migration(migrations.Migration):

    dependencies = [
        ('reeftrack_app', '0033_user'),
    ]

    operations = [
        migrations.RunPython(title_case_names, migrations.RunPython.noop),
    ]
