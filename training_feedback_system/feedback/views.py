from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse, FileResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from functools import wraps
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

import os
import uuid
import secrets

# Update local imports to use relative imports
from .models import TrainingSession, FeedbackResponse, Trainer, FeedbackReport

# Standard library imports - Load these immediately
import json
import os
import tempfile
import shutil
import base64
from io import BytesIO
import traceback
import logging

# Heavy imports are loaded lazily inside the functions that still require them.

# Configure logging
logger = logging.getLogger(__name__)


# ===== Utility Functions for Duplicate Prevention =====

def get_client_ip(request):
    """
    Get the client's IP address from the request.
    Handles proxy headers like X-Forwarded-For.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, get the first one
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def generate_submission_token():
    """Generate a unique token for form submission tracking"""
    return secrets.token_urlsafe(48)


def check_existing_submission(session, ip_address, participant_name):
    """
    Check if an identical/duplicate submission exists for this session.
    
    Returns:
        dict with 'exists' (bool) and 'message' (str)
    """
    from datetime import timedelta
    
    # Time window to check for duplicates (5 minutes)
    time_window = timezone.now() - timedelta(minutes=5)
    
    # Check if same participant submitted within time window (for named participants)
    if participant_name and participant_name != 'Anonymous':
        existing = FeedbackResponse.objects.filter(
            session=session,
            participant_name=participant_name,
            submitted_at__gte=time_window,
            is_duplicate=False  # Don't count already marked duplicates
        ).first()
        
        if existing:
            return {
                'exists': True,
                'message': f'You have already submitted feedback for this session. Please wait before submitting again.',
                'type': 'rate_limit'
            }
    
    # Check if same IP address already submitted within time window
    if ip_address:
        existing = FeedbackResponse.objects.filter(
            session=session,
            ip_address=ip_address,
            submitted_at__gte=time_window,
            is_duplicate=False  # Don't count already marked duplicates
        ).first()
        
        if existing:
            return {
                'exists': True,
                'message': 'A submission from your device has already been recorded. Thank you!',
                'type': 'duplicate'
            }
    
    return {'exists': False, 'message': '', 'type': None}


# --- Remove minimal admin authentication system ---
# Removed: is_admin_authenticated, custom session logic, and old admin_required
# Use Django's built-in authentication and the admin_required decorator from decorators.py

from .decorators import admin_required

# --- End minimal admin authentication system ---

def home(request):
    """
    Public Home page view.
    """
    return render(request, 'home.html')

# Add rate limiting and caching to public endpoints
@csrf_protect
def public_session_list(request):
    """
    Display a list of all training sessions for public feedback submission.
    Args:
        request (HttpRequest): The HTTP request object.
    Returns:
        HttpResponse: Rendered HTML page with the list of sessions.
    """
    try:
        sessions = TrainingSession.objects.filter(is_active=True).select_related('trainer')
        return render(request, 'feedback/public_session_list.html', {'sessions': sessions})
    except Exception as e:
        logger.error(f"Error in public_session_list: {str(e)}")
        messages.error(request, 'Unable to load sessions. Please try again later.')
        return redirect('feedback:home')

@admin_required
def feedback_success(request):
    """
    Render a success page after feedback submission.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for feedback success.
    """
    return render(request, 'feedback_success.html')

# Optimize dashboard queries and add caching
@admin_required
def dashboard(request):
    """
    Display the admin dashboard with summary statistics.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for the dashboard.
    """
    try:
        # Optimize queries with select_related and prefetch_related
        recent_sessions = (
            TrainingSession.objects
            .select_related('trainer')
            .prefetch_related('feedbackresponse_set')
            .order_by('-date')[:10]
        )

        top_trainers = (
            Trainer.objects
            .annotate(session_count=Count('trainingsession'))
            .order_by('-session_count')[:5]
        )

        dashboard_data = {
            'total_sessions': TrainingSession.objects.count(),
            'total_trainers': Trainer.objects.count(),
            'total_feedback': FeedbackResponse.objects.count(),
            'recent_sessions': list(recent_sessions),
            'top_trainers': list(top_trainers),
        }
    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        messages.error(request, 'Error loading dashboard data.')
        return redirect('feedback:error')

    return render(request, 'feedback/dashboard.html', dashboard_data)

@admin_required
def session_list(request):
    """
    List all training sessions for admin users with pagination.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page with paginated session list.
    """
    sessions = TrainingSession.objects.all().select_related('trainer')
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'feedback/session_list.html', {'page_obj': page_obj})

@admin_required
def create_session(request):
    """
    Create a new training session.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for session creation or redirect on success.
    """
    if request.method == 'POST':
        form = TrainingSessionForm(request.POST)
        trainer_name = request.POST.get('trainer_name')
        if trainer_name:
            trainer, _ = Trainer.objects.get_or_create(name=trainer_name, defaults={'email': '', 'phone': '', 'specialization': '', 'is_active': True})
            post = request.POST.copy()
            post['trainer'] = getattr(trainer, 'id', None)
            form = TrainingSessionForm(post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Training session created successfully!')
            return redirect('feedback:session_list')
    else:
        form = TrainingSessionForm()
    return render(request, 'feedback/create_session.html', {'form': form})

@admin_required
def session_detail(request, session_id):
    """
    Show details and feedback responses for a specific session.

    Args:
        request (HttpRequest): The HTTP request object.
        session_id (int): The ID of the training session.

    Returns:
        HttpResponse: Rendered HTML page with session details.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    feedback_responses = FeedbackResponse.objects.filter(session=session)
    response_count = feedback_responses.count()

    FEEDBACK_QUESTIONS = [
        "The training met my expectations",
        "I will be able to apply the knowledge learned",
        "The content was organized and easy to follow",
        "The trainer was knowledgeable",
        "Training was relevant to my needs",
        "Instructions were clear and understandable",
        "Length and timing of training was sufficient",
        "Overall, the session was very good"
    ]
    category_image_pairs = []  # Chart rendering disabled in this low-memory deployment

    SENTIMENT_LABELS = ['Strongly Agree', 'Agree', 'Neutral', 'Disagree', 'Strongly Disagree']
    # Build a matrix: sentiment as rows, questions as columns
    sentiment_matrix = {label: [] for label in SENTIMENT_LABELS}
    for i, question in enumerate(FEEDBACK_QUESTIONS, start=1):
        ratings = [getattr(resp, f'rating_{i}') for resp in feedback_responses]
        counts = {label: 0 for label in SENTIMENT_LABELS}
        for rating in ratings:
            if rating == 5:
                counts['Strongly Agree'] += 1
            elif rating == 4:
                counts['Agree'] += 1
            elif rating == 3:
                counts['Neutral'] += 1
            elif rating == 2:
                counts['Disagree'] += 1
            elif rating == 1:
                counts['Strongly Disagree'] += 1
        for label in SENTIMENT_LABELS:
            sentiment_matrix[label].append(counts[label])

    return render(request, 'feedback/session_detail.html', {
        'session': session,
        'feedback_responses': feedback_responses,
        'response_count': response_count,
        'category_image_pairs': category_image_pairs,
        'sentiment_matrix': sentiment_matrix,
        'feedback_questions': FEEDBACK_QUESTIONS,
        'sentiment_labels': SENTIMENT_LABELS,
    })

@admin_required
def trainer_list(request):
    """
    List all trainers with pagination.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page with paginated trainer list.
    """
    trainers = Trainer.objects.all()
    paginator = Paginator(trainers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'feedback/trainer_list.html', {'page_obj': page_obj})

@admin_required
def create_trainer(request):
    """
    Create a new trainer profile.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for trainer creation or redirect on success.
    """
    if request.method == 'POST':
        form = TrainerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trainer profile created successfully!')
            return redirect('feedback:trainer_list')
    else:
        form = TrainerForm()
    return render(request, 'feedback/create_trainer.html', {'form': form})

@admin_required
def edit_trainer(request, trainer_id):
    """
    Edit an existing trainer profile.

    Args:
        request (HttpRequest): The HTTP request object.
        trainer_id (int): The ID of the trainer.

    Returns:
        HttpResponse: Rendered HTML page for editing trainer.
    """
    trainer = get_object_or_404(Trainer, id=trainer_id)
    if request.method == 'POST':
        form = TrainerForm(request.POST, instance=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trainer updated successfully!')
            return redirect('feedback:trainer_list')
    else:
        form = TrainerForm(instance=trainer)
    return render(request, 'feedback/edit_trainer.html', {'form': form, 'trainer': trainer})

@admin_required
def report_detail(request, session_id):
    """
    Show the report detail page for a session (stub).

    Args:
        request (HttpRequest): The HTTP request object.
        session_id (int): The ID of the training session.

    Returns:
        HttpResponse: Rendered HTML page for report detail.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    report = None
    ai_analysis_data = None
    return render(request, 'feedback/report_detail.html', {'session': session, 'report': report, 'ai_analysis_data': ai_analysis_data})

@admin_required
def generate_report(request, session_id):
    """
    Generate a report for a session (dummy implementation).

    Args:
        request (HttpRequest): The HTTP request object.
        session_id (int): The ID of the training session.

    Returns:
        HttpResponse: Redirect to session detail page.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    messages.success(request, 'Report generated (dummy implementation).')
    return redirect('feedback:session_detail', session_id=session_id)

@admin_required
def download_report(request, session_id):
    """
    Download a report for a session.

    This deployment is running in a low-memory environment, so report generation is disabled.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    messages.warning(request, 'Report download is unavailable in the current deployment due to memory limits.')
    return redirect('feedback:session_detail', session_id=session_id)

@admin_required
def delete_session(request, session_id):
    """
    Delete a training session after confirmation.

    Args:
        request (HttpRequest): The HTTP request object.
        session_id (int): The ID of the training session.

    Returns:
        HttpResponse: Rendered confirmation page or redirect on success.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Training session deleted successfully!')
        return redirect('feedback:session_list')
    return render(request, 'feedback/delete_session_confirm.html', {'session': session})

@admin_required
def session_report_email(request, session_id):
    """
    Generate and display a session report email (optionally send email).

    Args:
        request (HttpRequest): The HTTP request object.
        session_id (int): The ID of the training session.

    Returns:
        HttpResponse: Rendered HTML page with report email content.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    feedback_responses = FeedbackResponse.objects.filter(session=session)
    if feedback_responses.exists():
        avg_rating = round(sum([r.get_average_rating() for r in feedback_responses]) / feedback_responses.count(), 2)
    else:
        avg_rating = 0
    report_context = {
        'trainer_name': session.trainer.name,
        'session_title': session.session_title,
        'date': session.date.strftime('%b %d, %Y'),
        'institution': session.institution,
        'audience': session.audience,
        'avg_rating': avg_rating,
    }
    report_text = render_to_string('feedback/session_report_email.txt', report_context)
    if request.method == 'POST':
        # Optionally, send email here
        messages.success(request, 'Report email generated!')
    return render(request, 'feedback/session_report_email.html', {
        'session': session,
        'report_text': report_text,
    })

@admin_required
def feedback_summary(request):
    """
    Display a summary of feedback for all sessions, showing only basic stats for performance.
    """
    sessions = TrainingSession.objects.all().select_related('trainer')
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    summary_sessions = []
    for session in page_obj:
        feedbacks = FeedbackResponse.objects.filter(session=session)
        avg_rating = feedbacks.aggregate(avg=Avg(
            (F('rating_1') + F('rating_2') + F('rating_3') +
             F('rating_4') + F('rating_5') + F('rating_6') +
             F('rating_7') + F('rating_8')) / 8
        ))['avg']
        summary_sessions.append({
            'session': session,
            'feedback_count': feedbacks.count(),
            'average_rating': round(avg_rating, 2) if avg_rating else 'N/A',
        })

    return render(request, 'feedback/feedback_summary.html', {
        'sessions': summary_sessions,
        'page_obj': page_obj,
    })

def safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0

def generate_chart_data(analysis):
    chart_data = {}
    for qkey, qanalysis in analysis['question_analyses'].items():
        chart_data[qkey] = {
            'labels': ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"],
            'counts': [qanalysis['categorical_counts'][cat] for cat in ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]],
        }
    return chart_data

from .forms import FeedbackForm, TrainerForm, TrainingSessionForm, GmailAuthenticationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Avg, F
from django.core.cache import cache

@admin_required
def delete_trainer(request, trainer_id):
    """
    Delete a trainer after confirmation.
    """
    trainer = get_object_or_404(Trainer, id=trainer_id)
    if request.method == 'POST':
        trainer.delete()
        messages.success(request, 'Trainer deleted successfully!')
        return redirect('feedback:trainer_list')
    return render(request, 'feedback/delete_trainer_confirm.html', {'trainer': trainer})

@admin_required
def toggle_session_active(request, session_id):
    """
    Toggle the active status of a training session.

    Args:
        request (HttpRequest): The HTTP request object.
        session_id (int): The ID of the training session.

    Returns:
        HttpResponse: Redirect to session list page.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    session.is_active = not session.is_active
    session.save()
    messages.success(request, f'Session "{session.session_title}" active status changed.')
    return redirect('feedback:session_list')

@admin_required
def download_charts(request, session_id):
    """
    Download charts for session feedback.

    This deployment is running in a low-memory environment, so chart generation is disabled.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    messages.warning(request, 'Chart download is unavailable in the current deployment due to memory limits.')
    return redirect('feedback:session_detail', session_id=session_id)

# --- Helper to enforce rating field labels and help text ---
def set_rating_labels(form):
    RATING_LABELS = [
        ("1. The training met my expectations", "Please rate how well the training aligned with your expectations"),
        ("2. I will be able to apply the knowledge learned", "Rate your ability to apply what you learned"),
        ("3. The content was organized and easy to follow", "Rate how well organized and clear the content was"),
        ("4. The trainer was knowledgeable", "Rate the trainer's expertise and knowledge"),
        ("5. Training was relevant to my needs", "Rate how relevant the training was to your needs"),
        ("6. Instructions were clear and understandable", "Rate how clear and understandable the instructions were"),
        ("7. Length and timing of training was sufficient", "Rate if the duration and timing were appropriate"),
        ("8. Overall, the session was very good", "Rate your overall satisfaction with the session"),
    ]
    for i, (label, help_text) in enumerate(RATING_LABELS, 1):
        field = form.fields.get(f'rating_{i}')
        if field:
            field.label = label
            field.help_text = help_text
    return form

def session_feedback(request, session_id):
    """
    Display a simple feedback form for a session and handle submission.
    Renders the unified feedback_form.html template with custom radio buttons.
    
    Implements duplicate submission prevention:
    - Tracks IP addresses and participant names
    - Prevents multiple submissions from same source within 5 minutes
    - Marks suspicious submissions as duplicates without deleting data
    """
    from django.shortcuts import get_object_or_404, redirect, render
    from django.contrib import messages
    
    session = get_object_or_404(TrainingSession, id=session_id, is_active=True)
    
    if request.method == 'POST':
        # Get client IP address for duplicate tracking
        client_ip = get_client_ip(request)
        
        # Check for existing submissions before processing form
        duplicate_check = check_existing_submission(
            session=session,
            ip_address=client_ip,
            participant_name=request.POST.get('participant_name', '').strip()
        )
        
        if duplicate_check['exists']:
            messages.warning(request, duplicate_check['message'])
            # Redirect back to the form instead of rejecting
            return redirect('feedback:session_feedback', session_id=session_id)
        
        form = FeedbackForm(request.POST)
        form = set_rating_labels(form)
        
        if form.is_valid():
            try:
                feedback = form.save(commit=False)
                feedback.session = session
                feedback.ip_address = client_ip
                # Generate submission token to prevent double-submit from same form
                feedback.submission_token = generate_submission_token()
                
                # Save will trigger clean() which will check for duplicates
                feedback.save()
                
                logger.info(
                    f"Feedback submitted for session {session_id} by {feedback.participant_name} "
                    f"from IP {client_ip}"
                )
                
                return render(request, 'feedback/feedback_success_public.html', {
                    'session': session
                })
            except Exception as e:
                logger.error(f"Error saving feedback: {str(e)}")
                messages.error(
                    request, 
                    'An error occurred while saving your feedback. Please try again.'
                )
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeedbackForm(initial={
            'session': session.id,
            'submission_token': generate_submission_token()
        })
        form = set_rating_labels(form)
    
    rating_field_names = [f'rating_{i}' for i in range(1, 9)]
    
    return render(request, 'feedback/feedback_form.html', {
        'feedback_form': form,
        'session': session,
        'rating_field_names': rating_field_names,
    })

# Deprecated: session_feedback.html is no longer used. All feedback forms use feedback_form.html for consistent UI.

# The following view is a stub to prevent import errors. Remove or implement as needed.
def tabbed_feedback_forms(request):
    from django.http import HttpResponse
    return HttpResponse("Tabbed feedback forms view is not implemented yet.")

# The following view is a stub to prevent import errors. Remove or implement as needed.
def feedback_view(request):
    from django.http import HttpResponse
    return HttpResponse("Feedback view is not implemented yet.")
