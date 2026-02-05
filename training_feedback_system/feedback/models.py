from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class Trainer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class TrainingSession(models.Model):
    session_title = models.CharField(max_length=200)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    date = models.DateField()
    institution = models.CharField(max_length=200, blank=True)
    audience = models.CharField(max_length=200, blank=True, help_text="e.g., BBA students, IT professionals")
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('2.0'))
    max_participants = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Add this line
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.session_title} - {self.trainer.name}"

    def get_feedback_count(self):
        # type: () -> int
        return self.feedbackresponse_set.count()  # type: ignore[attr-defined]

    def get_average_rating(self):
        # type: () -> float
        responses = self.feedbackresponse_set.all()  # type: ignore[attr-defined]
        if not responses:
            return 0
        total_ratings = 0
        count = 0
        for response in responses:
            ratings = [
                response.rating_1, response.rating_2, response.rating_3, 
                response.rating_4, response.rating_5, response.rating_6, 
                response.rating_7, response.rating_8
            ]
            total_ratings += sum(rating for rating in ratings if rating is not None)
            count += len([rating for rating in ratings if rating is not None])
        return round(total_ratings / count, 2) if count > 0 else 0

    def has_open_feedback(self):
        """
        Returns True if the session is active and the date is today or in the future.
        """
        from django.utils import timezone
        return self.is_active and self.date >= timezone.now().date()

    class Meta:
        ordering = ['-date']

class FeedbackResponse(models.Model):
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)
    participant_name = models.CharField(max_length=100, blank=True, default='Anonymous')
    
    # 8 Rating Questions (1-5 scale)
    rating_1 = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Met Expectations",
        help_text="The training met my expectations"
    )
    rating_2 = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="I will be able to apply the knowledge learned"
    )
    rating_3 = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="The content was organized and easy to follow"
    )
    rating_4 = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="The trainer was knowledgeable"
    )
    rating_5 = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Training was relevant to my needs"
    )
    rating_6 = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Instructions were clear and understandable"
    )
    rating_7 = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Length and timing of training was sufficient"
    )
    rating_8 = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Overall, the session was very good"
    )
    
    # Open-ended Questions
    key_learnings = models.TextField(help_text="What are the 3–5 key learnings from today's session?")
    missing_elements = models.TextField(
        blank=True, 
        help_text="In your opinion, what was missing in the session?"
    )
    
    # Meta
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def clean(self):
        """Validate feedback response data"""
        try:
            for i in range(1, 9):
                rating = getattr(self, f'rating_{i}')
                if rating is None:
                    raise ValidationError(f'Rating {i} is required')
                if not (1 <= rating <= 5):
                    raise ValidationError(f'Rating {i} must be between 1 and 5')
        except Exception as e:
            logger.error(f"Validation error in FeedbackResponse: {str(e)}")
            raise

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_average_rating(self):
        ratings = [
            self.rating_1, self.rating_2, self.rating_3, self.rating_4,
            self.rating_5, self.rating_6, self.rating_7, self.rating_8
        ]
        return round(sum(ratings) / len(ratings), 2)

    def __str__(self):
        return f"Feedback for {self.session.session_title} by {self.participant_name}"

    class Meta:
        ordering = ['-submitted_at']

class FeedbackReport(models.Model):
    session = models.OneToOneField(TrainingSession, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    openai_analysis = models.TextField(blank=True)
    word_document = models.FileField(upload_to='reports/', blank=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Report for {self.session.session_title}"

    class Meta:
        ordering = ['-generated_at']

class FeedbackImage(models.Model):
    # The 'id' field is automatically created by Django as the primary key.
    # If you see errors about 'id', ensure migrations are applied:
    #   python manage.py makemigrations && python manage.py migrate
    image = models.ImageField(upload_to='feedback_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Detected ratings
    rating_1 = models.IntegerField(null=True, blank=True)
    rating_2 = models.IntegerField(null=True, blank=True)
    rating_3 = models.IntegerField(null=True, blank=True)
    rating_4 = models.IntegerField(null=True, blank=True)
    rating_5 = models.IntegerField(null=True, blank=True)
    rating_6 = models.IntegerField(null=True, blank=True)
    rating_7 = models.IntegerField(null=True, blank=True)
    rating_8 = models.IntegerField(null=True, blank=True)
    ocr_text = models.TextField(blank=True)

    def __str__(self):
        return f"FeedbackImage {getattr(self, 'id', 'unknown')}"

class Feedback(models.Model):
    session = models.ForeignKey('TrainingSession', on_delete=models.CASCADE, null=True, blank=True, related_name='feedbacks')
    participant_name = models.CharField(max_length=100, blank=True)
    rating_1 = models.IntegerField()
    rating_2 = models.IntegerField()
    rating_3 = models.IntegerField()
    rating_4 = models.IntegerField()
    rating_5 = models.IntegerField()
    rating_6 = models.IntegerField()
    rating_7 = models.IntegerField()
    rating_8 = models.IntegerField()
    key_learnings = models.TextField(blank=True)
    missing_elements = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.session:
            return f"Feedback for {self.session.session_title} by {self.participant_name or 'Anonymous'} on {self.submitted_at:%Y-%m-%d}"
        return f"Feedback by {self.participant_name or 'Anonymous'} on {self.submitted_at:%Y-%m-%d}"
