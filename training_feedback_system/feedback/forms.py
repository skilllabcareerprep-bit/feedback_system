from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div, HTML
from .models import FeedbackResponse, Trainer, TrainingSession, FeedbackImage, Feedback
import logging
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class FeedbackForm(forms.ModelForm):
    RATING_CHOICES = [
        (1, '1 - Strongly Disagree'),
        (2, '2 - Disagree'),
        (3, '3 - Neutral'),
        (4, '4 - Agree'),
        (5, '5 - Strongly Agree'),
    ]

    rating_1 = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="1. The training met my expectations",
        help_text="Please rate how well the training aligned with your expectations"
    )
    rating_2 = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="2. I will be able to apply the knowledge learned",
        help_text="Rate your ability to apply what you learned"
    )
    rating_3 = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="3. The content was organized and easy to follow",
        help_text="Rate how well organized and clear the content was"
    )
    rating_4 = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="4. The trainer was knowledgeable",
        help_text="Rate the trainer's expertise and knowledge"
    )
    rating_5 = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="5. Training was relevant to my needs",
        help_text="Rate how relevant the training was to your needs"
    )
    rating_6 = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="6. Instructions were clear and understandable",
        help_text="Rate how clear and understandable the instructions were"
    )
    rating_7 = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="7. Length and timing of training was sufficient",
        help_text="Rate if the duration and timing were appropriate"
    )
    rating_8 = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="8. Overall, the session was very good",
        help_text="Rate your overall satisfaction with the session"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'feedback-form'
        self.helper.layout = Layout(
            Div(
                Field('participant_name', css_class='mb-3'),
                css_class='participant-info'
            ),
            HTML("<h3 class='mt-4 mb-3'>Rating Questions</h3>"),
            Div(
                Field('rating_1', template='feedback/rating_template.html'),
                Field('rating_2', template='feedback/rating_template.html'),
                Field('rating_3', template='feedback/rating_template.html'),
                Field('rating_4', template='feedback/rating_template.html'),
                css_class='ratings-group-1'
            ),
            Div(
                Field('rating_5', template='feedback/rating_template.html'),
                Field('rating_6', template='feedback/rating_template.html'),
                Field('rating_7', template='feedback/rating_template.html'),
                Field('rating_8', template='feedback/rating_template.html'),
                css_class='ratings-group-2'
            ),
            HTML("<h3 class='mt-4 mb-3'>Additional Feedback</h3>"),
            Div(
                Field('key_learnings', css_class='mb-3'),
                Field('missing_elements', css_class='mb-3'),
                css_class='text-feedback'
            ),
        )

    class Meta:
        model = FeedbackResponse
        fields = [
            'participant_name',
            'rating_1', 'rating_2', 'rating_3', 'rating_4',
            'rating_5', 'rating_6', 'rating_7', 'rating_8',
            'key_learnings', 'missing_elements'
        ]
        widgets = {
            'participant_name': forms.TextInput(attrs={
                'placeholder': 'Enter your name (optional)',
                'class': 'form-control'
            }),
            'key_learnings': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Please list the main things you learned during this session...',
                'class': 'form-control'
            }),
            'missing_elements': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Please share what you think could have been improved or added...',
                'class': 'form-control'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        try:
            for i in range(1, 9):
                rating_key = f'rating_{i}'
                rating = cleaned_data.get(rating_key)
                if rating in (None, ''):
                    self.add_error(rating_key, f'Rating {i} is required')
                elif not (1 <= int(rating) <= 5):
                    self.add_error(rating_key, f'Rating for question {i} must be between 1 and 5')
        except Exception as e:
            logger.error(f"Form validation error: {str(e)}")
            raise
        return cleaned_data

class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['name', 'email', 'phone', 'specialization', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'trainer-form'
        self.helper.layout = Layout(
            Div(
                Field('name', css_class='mb-3'),
                Field('email', css_class='mb-3'),
                Field('phone', css_class='mb-3'),
                Field('specialization', css_class='mb-3'),
                Field('is_active', css_class='mb-3'),
                css_class='trainer-fields'
            ),
            Div(
                Submit('submit', 'Save Trainer', css_class='btn btn-primary'),
                css_class='form-actions'
            )
        )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any non-digit characters
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 10:
                raise ValidationError('Phone number must have at least 10 digits')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if Trainer.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('This email is already registered')
        return email

class TrainingSessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ['session_title', 'trainer', 'date', 'institution', 'audience', 'duration_hours', 'max_participants', 'is_active']
        widgets = {
            'session_title': forms.TextInput(attrs={'class': 'form-control'}),
            'trainer': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'audience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., BBA students, IT professionals'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'session-form'
        self.helper.layout = Layout(
            Div(
                Field('session_title', css_class='mb-3'),
                Field('trainer', css_class='mb-3'),
                Field('date', css_class='mb-3'),
                Field('institution', css_class='mb-3'),
                Field('audience', css_class='mb-3'),
                Field('duration_hours', css_class='mb-3'),
                Field('max_participants', css_class='mb-3'),
                Field('is_active', css_class='mb-3'),
                css_class='session-fields'
            ),
            Div(
                Submit('submit', 'Save Session', css_class='btn btn-primary'),
                css_class='form-actions'
            )
        )

class FeedbackImageUploadForm(forms.Form):
    image_file = forms.ImageField(label='Upload Feedback Form Image')
    session = forms.ModelChoiceField(queryset=TrainingSession.objects.all(), label='Session')

class FeedbackImageForm(forms.ModelForm):
    class Meta:
        model = FeedbackImage
        fields = ['image']

class GmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Gmail', max_length=254, widget=forms.EmailInput(attrs={'autofocus': True}))

    def clean_username(self):
        email = self.cleaned_data.get('username')
        if not email or not email.endswith('@gmail.com'):
            raise forms.ValidationError('Only Gmail addresses are allowed.')
        return email
