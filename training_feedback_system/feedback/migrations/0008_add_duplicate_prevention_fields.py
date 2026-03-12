# Generated migration to add duplicate prevention fields to FeedbackResponse

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0007_add_audience_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackresponse',
            name='submission_token',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Unique token to prevent duplicate submissions',
                max_length=64,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name='feedbackresponse',
            name='is_duplicate',
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text='Whether this is marked as a potential duplicate submission',
            ),
        ),
        migrations.AddIndex(
            model_name='feedbackresponse',
            index=models.Index(fields=['session', 'ip_address', 'is_duplicate'], name='feedback_f_session_idx1'),
        ),
        migrations.AddIndex(
            model_name='feedbackresponse',
            index=models.Index(fields=['submitted_at', 'session'], name='feedback_f_submit_idx1'),
        ),
    ]
