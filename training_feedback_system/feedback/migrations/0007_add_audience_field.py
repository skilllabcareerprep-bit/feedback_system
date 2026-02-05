# Generated migration to add audience field to TrainingSession

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0006_rename_location_to_institution'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingsession',
            name='audience',
            field=models.CharField(
                blank=True,
                help_text='e.g., BBA students, IT professionals',
                max_length=200
            ),
        ),
    ]
