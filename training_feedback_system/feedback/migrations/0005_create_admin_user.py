from django.db import migrations
from django.contrib.auth.models import User


def create_admin_user(apps, schema_editor):
    """Create admin superuser"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='Feedback@2026'
        )
        print("✓ Admin superuser created")
    else:
        # Update existing admin password
        user = User.objects.get(username='admin')
        user.set_password('Feedback@2026')
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print("✓ Admin superuser password updated")


def reverse_create_admin(apps, schema_editor):
    """Delete admin user on migration reversal"""
    User.objects.filter(username='admin').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0004_feedback_session'),
    ]

    operations = [
        migrations.RunPython(create_admin_user, reverse_create_admin),
    ]
