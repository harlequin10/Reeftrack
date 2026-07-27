from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reeftrack_app', '0025_populate_sarangani_province'),
    ]

    operations = [
        migrations.AlterField(
            model_name='municipality',
            name='province',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='municipalities', to='reeftrack_app.province'),
        ),
    ]
