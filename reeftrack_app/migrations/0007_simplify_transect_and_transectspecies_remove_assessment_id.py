from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reeftrack_app', '0006_assessment_excel_file_assessment_thesis_pdf_and_more'),
    ]

    operations = [
        # --- Assessment: remove assessment_id and excel_file ---
        migrations.RemoveField(
            model_name='assessment',
            name='assessment_id',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='excel_file',
        ),

        # --- Transect: replace 8 lat/lng fields + avg_cover with simplified fields ---
        migrations.RemoveField(
            model_name='transect',
            name='shallow_start_lat',
        ),
        migrations.RemoveField(
            model_name='transect',
            name='shallow_start_lng',
        ),
        migrations.RemoveField(
            model_name='transect',
            name='shallow_end_lat',
        ),
        migrations.RemoveField(
            model_name='transect',
            name='shallow_end_lng',
        ),
        migrations.RemoveField(
            model_name='transect',
            name='deep_start_lat',
        ),
        migrations.RemoveField(
            model_name='transect',
            name='deep_start_lng',
        ),
        migrations.RemoveField(
            model_name='transect',
            name='deep_end_lat',
        ),
        migrations.RemoveField(
            model_name='transect',
            name='deep_end_lng',
        ),
        migrations.RemoveField(
            model_name='transect',
            name='shallow_avg_cover',
        ),
        migrations.RemoveField(
            model_name='transect',
            name='deep_avg_cover',
        ),
        migrations.AddField(
            model_name='transect',
            name='shallow_lat',
            field=models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transect',
            name='shallow_lng',
            field=models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transect',
            name='shallow_excel',
            field=models.FileField(blank=True, null=True, upload_to='assessments/transect_excel/'),
        ),
        migrations.AddField(
            model_name='transect',
            name='deep_lat',
            field=models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transect',
            name='deep_lng',
            field=models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transect',
            name='deep_excel',
            field=models.FileField(blank=True, null=True, upload_to='assessments/transect_excel/'),
        ),

        # --- TransectSpecies: replace 3 cover fields with depth + cover ---
        migrations.RemoveField(
            model_name='transectspecies',
            name='shallow_cover',
        ),
        migrations.RemoveField(
            model_name='transectspecies',
            name='deep_cover',
        ),
        migrations.RemoveField(
            model_name='transectspecies',
            name='mean_cover',
        ),
        # First drop old unique_together before adding depth field
        migrations.AlterUniqueTogether(
            name='transectspecies',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='transectspecies',
            name='depth',
            field=models.CharField(
                choices=[('shallow', 'Shallow'), ('deep', 'Deep')],
                default='shallow',
                max_length=10,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transectspecies',
            name='cover',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=7),
        ),
        # Set new unique_together with depth
        migrations.AlterUniqueTogether(
            name='transectspecies',
            unique_together={('transect', 'species', 'depth')},
        ),
    ]
