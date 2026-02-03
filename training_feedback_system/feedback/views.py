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

# Update local imports to use relative imports
from .models import TrainingSession, FeedbackResponse, Trainer, FeedbackReport, FeedbackImage
from .utils import FeedbackAnalyzer
from .rating_detector import AdvancedRatingDetector

# Third-party imports
try:
    import cv2
except ImportError:
    raise ImportError("Please install opencv-python: pip install opencv-python")

try:
    import pytesseract
    import qrcode
    import numpy as np
    import pandas as pd
except ImportError as e:
    raise ImportError(f"Missing required package: {str(e)}. Please install all required packages.")

# Standard library imports
import json
import os
import tempfile
import shutil
import base64
from io import BytesIO
from PIL import Image
from rapidfuzz import fuzz, process
import traceback
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Tesseract configuration
def configure_tesseract():
    """Configure Tesseract OCR path - optional, won't fail if not available"""
    try:
        tesseract_path = shutil.which('tesseract')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Default Windows path - adjust if needed
            windows_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(windows_path):
                pytesseract.pytesseract.tesseract_cmd = windows_path
            # Don't raise error - Tesseract is optional on production
    except Exception as e:
        # Tesseract OCR is optional - log warning but don't fail
        print(f"Warning: Tesseract-OCR not found: {e}")
        pass

# Call configuration on module load (but don't fail if not available)
try:
    configure_tesseract()
except Exception:
    pass

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
    category_image_pairs = []
    from .utils import create_rating_chart
    for i, question in enumerate(FEEDBACK_QUESTIONS, start=1):
        img_url = create_rating_chart(feedback_responses, question, i)
        category_image_pairs.append((question, img_url))

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
    Download a report for a session (not implemented).

    Args:
        request (HttpRequest): The HTTP request object.
        session_id (int): The ID of the training session.

    Returns:
        HttpResponse: Plain text response for download.
    """
    from .utils import generate_word_report, analyze_feedback_with_openai
    session = get_object_or_404(TrainingSession, id=session_id)
    feedback_responses = session.feedbackresponse_set.all()
    # Optionally run AI analysis (can be skipped or cached)
    ai_analysis = analyze_feedback_with_openai(feedback_responses)
    report_path, report_filename = generate_word_report(session, feedback_responses, ai_analysis)
    if not os.path.exists(report_path):
        return HttpResponse('Report generation failed.', content_type='text/plain')
    response = FileResponse(open(report_path, 'rb'), as_attachment=True, filename=report_filename)
    return response

@admin_required
def download_feedback_qr(request, session_id):
    """
    Download a QR code for the feedback form of a session.

    Args:
        request (HttpRequest): The HTTP request object.
        session_id (int): The ID of the training session.

    Returns:
        FileResponse: PNG image file of the QR code.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    try:
        feedback_url = request.build_absolute_uri(
            f"/sessions/{getattr(session, 'id', None)}/feedback/"
        )
        qr = qrcode.QRCode(
            version=1,
            error_correction=QR_ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(feedback_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        # Save QR code image to buffer (PIL Image)
        try:
            img.save(buf)
        except Exception:
            img.save(buf)
        buf.seek(0)
        filename = f"feedback_session_{getattr(session, 'id', 'unknown')}_qr.png"
        response = FileResponse(buf, as_attachment=True, filename=filename)
        return response
    except Exception as e:
        messages.error(request, f'Error generating QR code: {str(e)}')
        return redirect('feedback:session_detail', session_id=getattr(session, 'id', None))

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
        'location': session.location,
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

# Add proper error handling to upload_feedback_image
@ensure_csrf_cookie
def upload_feedback_image(request):
    """
    Handle feedback form image upload, process the image, and extract ratings using the AdvancedRatingDetector.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: JSON response with extracted feedback, visualization, and debug info.
    """
    debug_info = {
        'request_method': request.method,
        'content_type': request.content_type,
        'has_file': 'image_file' in request.FILES,
        'session_id': request.POST.get('session'),
        'tesseract_path': pytesseract.pytesseract.tesseract_cmd,
        'tesseract_exists': os.path.isfile(pytesseract.pytesseract.tesseract_cmd),
    }

    if request.method == 'GET':
        form = FeedbackImageUploadForm()
        return render(request, 'feedback/upload_feedback_image.html', {'form': form})

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': f'Method {request.method} not allowed',
            'debug_info': debug_info
        })

    tmp_path = None
    try:
        session_id = request.POST.get('session')
        if not session_id or not session_id.isdigit():
            raise ValidationError('Please select a valid session.')

        session = get_object_or_404(TrainingSession, id=session_id)
        image_file = request.FILES.get('image_file')
        
        if not image_file:
            raise ValidationError('No image file received.')

        # Validate file size and type
        if image_file.size > settings.MAX_UPLOAD_SIZE:
            raise ValidationError('File size too large.')
            
        if not image_file.content_type.startswith('image/'):
            raise ValidationError('Invalid file type.')

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        img = cv2.imread(tmp_path)
        if img is None:
            raise ValidationError('Failed to read image file')

        detector = AdvancedRatingDetector()
        ratings, detection_debug = detector.detect_ratings(img)

        feedback_data = process_feedback_data(ratings)
        viz_img = detector.visualize_detections(img, ratings)
        viz_base64 = convert_image_to_base64(viz_img)
        
        confidence_stats = calculate_confidence_stats(ratings)

        return JsonResponse({
            'success': True,
            'feedback': feedback_data,
            'visualization': viz_base64,
            'debug_info': {
                **debug_info,
                'image_size': img.shape,
                'detection_info': detection_debug,
                'ratings_summary': confidence_stats
            }
        })

    except ValidationError as ve:
        return JsonResponse({
            'success': False,
            'error': str(ve),
            'debug_info': debug_info
        })
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing the image.',
            'debug_info': debug_info
        })
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.error(f"Error removing temp file: {str(e)}")

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

def process_feedback_data(ratings):
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
    
    feedback_data = []
    for row in range(8):
        row_rating = next((r for r in ratings if r['row'] == row), None)
        rating = row_rating['rating'] if row_rating else 0
        confidence = row_rating['confidence'] if row_rating else 0
        question = FEEDBACK_QUESTIONS[row] if row < len(FEEDBACK_QUESTIONS) else f"Question {row + 1}"
        feedback_data.append({
            'question': question,
            'rating': rating,
            'confidence': confidence
        })
    return feedback_data

def convert_image_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def calculate_confidence_stats(ratings):
    confidence_scores = [r['confidence'] for r in ratings]
    return {
        'total_detected': len(ratings),
        'confidence_min': min(confidence_scores) if confidence_scores else 0,
        'confidence_max': max(confidence_scores) if confidence_scores else 0,
        'confidence_avg': np.mean(confidence_scores) if confidence_scores else 0
    }

# Robust ERROR_CORRECT_L import and fallback
try:
    from qrcode.constants import ERROR_CORRECT_L
    QR_ERROR_CORRECT_L = ERROR_CORRECT_L
except ImportError:
    QR_ERROR_CORRECT_L = 1  # fallback to default value for error correction

from .forms import FeedbackForm, TrainerForm, TrainingSessionForm, GmailAuthenticationForm, FeedbackImageUploadForm, FeedbackImageForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Avg, F
from django.core.cache import cache

import pytesseract
from PIL import Image
import cv2
import numpy as np
from .models import FeedbackImage

def detect_ratings_from_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    pil_img = Image.fromarray(thresh)
    text = pytesseract.image_to_string(pil_img)
    import re
    ratings = {}
    for i in range(1, 9):
        pattern = rf"{i}\.\s.*?([5-1])"
        match = re.search(pattern, text)
        if match:
            ratings[f'rating_{i}'] = int(match.group(1))
        else:
            ratings[f'rating_{i}'] = None
    return ratings, text

def upload_feedback_image_legacy(request):
    """
    [LEGACY] Handle feedback form image upload, process the image, and extract ratings using the legacy method.
    Use 'upload_feedback_image' for the new AJAX/JSON-based upload.
    """
    if request.method == 'POST':
        form = FeedbackImageForm(request.POST, request.FILES)
        if form.is_valid():
            feedback_image = form.save()
            img_path = feedback_image.image.path
            ratings, ocr_text = detect_ratings_from_image(img_path)
            feedback_image.ocr_text = ocr_text
            for key, value in ratings.items():
                setattr(feedback_image, key, value)
            feedback_image.save()
            return render(request, 'feedback/upload_feedback_image.html', {
                'form': FeedbackImageForm(),
                'feedback_image': feedback_image,
                'ratings': ratings,
                'ocr_text': ocr_text,
            })
    else:
        form = FeedbackImageForm()
    return render(request, 'feedback/upload_feedback_image.html', {'form': form})

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
    Download charts for session feedback as a ZIP file.

    Args:
        request (HttpRequest): The HTTP request object.
        session_id (int): The ID of the training session.

    Returns:
        HttpResponse: ZIP file download response.
    """
    import zipfile
    from io import BytesIO
    from .utils import create_rating_chart
    session = get_object_or_404(TrainingSession, id=session_id)
    feedback_responses = FeedbackResponse.objects.filter(session=session)
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
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for i, question in enumerate(FEEDBACK_QUESTIONS, start=1):
            # Generate chart as raw PNG bytes
            from io import BytesIO
            import base64
            import matplotlib.pyplot as plt
            ratings = []
            for response in feedback_responses:
                rating_value = getattr(response, f'rating_{i}')
                ratings.append(rating_value)
            from collections import Counter
            rating_counts = Counter(ratings)
            plt.figure(figsize=(10, 6))
            categories = ['Strongly\nDisagree', 'Disagree', 'Neutral', 'Agree', 'Strongly\nAgree']
            values = [rating_counts.get(j, 0) for j in range(1, 6)]
            bars = plt.bar(categories, values, color='#4472C4')
            plt.title(question, fontsize=14, fontweight='bold', pad=20)
            plt.ylabel('Number of Responses')
            for bar, value in zip(bars, values):
                if value > 0:
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                            str(value), ha='center', va='bottom', fontweight='bold')
            plt.tight_layout()
            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            zip_file.writestr(f'question_{i}.png', buf.read())
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="session_{session_id}_charts.zip"'
    return response

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
    """
    from django.shortcuts import get_object_or_404, redirect, render
    from django.contrib import messages
    session = get_object_or_404(TrainingSession, id=session_id, is_active=True)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        form = set_rating_labels(form)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.session = session
            feedback.save()
            return render(request, 'feedback/feedback_success_public.html', {
                'session': session
            })
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeedbackForm(initial={'session': session.id})
        form = set_rating_labels(form)
    rating_field_names = [f'rating_{i}' for i in range(1, 9)]
    # Always render the unified feedback_form.html for consistent radio button UI
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
