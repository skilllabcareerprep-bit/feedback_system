import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class FeedbackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedback'
    verbose_name = 'Feedback System' 
