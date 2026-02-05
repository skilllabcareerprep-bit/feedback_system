# Generated migration to rename location field to institution

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0005_create_admin_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='trainingsession',
            old_name='location',
            new_name='institution',
        ),
    ]
