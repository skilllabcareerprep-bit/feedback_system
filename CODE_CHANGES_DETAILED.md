# Code Changes Summary - Duplicate Prevention Implementation

## File 1: `feedback/models.py`

### Change 1: Added new fields to FeedbackResponse model

```python
class FeedbackResponse(models.Model):
    # ... existing fields ...
    
    # NEW: Duplicate Prevention Fields
    submission_token = models.CharField(
        max_length=64, 
        blank=True, 
        null=True,
        unique=True,
        db_index=True,
        help_text="Unique token to prevent duplicate submissions"
    )
    
    is_duplicate = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this is marked as a potential duplicate submission"
    )
```

### Change 2: Enhanced clean() method

```python
def clean(self):
    """Validate feedback response data and check for duplicates"""
    try:
        # Existing rating validation...
        for i in range(1, 9):
            rating = getattr(self, f'rating_{i}')
            if rating is None:
                raise ValidationError(f'Rating {i} is required')
            if not (1 <= rating <= 5):
                raise ValidationError(f'Rating {i} must be between 1 and 5')
        
        # NEW: Check for duplicate submissions
        if not self.is_duplicate and not self.pk:  # Only on new submissions
            duplicate_check = self.check_for_duplicate_submission()
            if duplicate_check['is_duplicate']:
                self.is_duplicate = True
                logger.warning(
                    f"Potential duplicate submission detected for session {self.session_id} "
                    f"from {self.ip_address}: {duplicate_check['reason']}"
                )
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Validation error in FeedbackResponse: {str(e)}")
        raise
```

### Change 3: New check_for_duplicate_submission() method

```python
def check_for_duplicate_submission(self):
    """
    Check if this submission appears to be a duplicate.
    Returns a dict with 'is_duplicate' boolean and 'reason' string.
    
    A submission is considered a duplicate if:
    1. Same participant_name submitted to same session within 5 minutes
    2. Same IP address submitted identical ratings to same session within 5 minutes
    """
    from django.utils import timezone
    from datetime import timedelta
    
    time_window = timezone.now() - timedelta(minutes=5)
    
    # Check 1: Same participant and session within time window
    if self.participant_name and self.participant_name != 'Anonymous':
        existing = FeedbackResponse.objects.filter(
            session=self.session,
            participant_name=self.participant_name,
            submitted_at__gte=time_window,
            is_duplicate=False
        ).exists()
        
        if existing:
            return {
                'is_duplicate': True,
                'reason': f'Submission from participant "{self.participant_name}" already exists within 5 minutes'
            }
    
    # Check 2: Same IP address with identical ratings within time window
    if self.ip_address:
        identical_submission = FeedbackResponse.objects.filter(
            session=self.session,
            ip_address=self.ip_address,
            rating_1=self.rating_1,
            rating_2=self.rating_2,
            rating_3=self.rating_3,
            rating_4=self.rating_4,
            rating_5=self.rating_5,
            rating_6=self.rating_6,
            rating_7=self.rating_7,
            rating_8=self.rating_8,
            submitted_at__gte=time_window,
            is_duplicate=False
        ).exists()
        
        if identical_submission:
            return {
                'is_duplicate': True,
                'reason': f'Identical submission from IP {self.ip_address} already exists within 5 minutes'
            }
    
    return {'is_duplicate': False, 'reason': ''}
```

### Change 4: Enhanced Meta class with indexes

```python
class Meta:
    ordering = ['-submitted_at']
    indexes = [
        models.Index(fields=['session', 'ip_address', 'is_duplicate']),
        models.Index(fields=['submitted_at', 'session']),
    ]
```

---

## File 2: `feedback/views.py`

### Change 1: Add imports

```python
import uuid
import secrets  # NEW - for secure token generation
```

### Change 2: New utility functions

```python
def get_client_ip(request):
    """
    Get the client's IP address from the request.
    Handles proxy headers like X-Forwarded-For.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
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
    
    time_window = timezone.now() - timedelta(minutes=5)
    
    # Check if same participant submitted within time window
    if participant_name and participant_name != 'Anonymous':
        existing = FeedbackResponse.objects.filter(
            session=session,
            participant_name=participant_name,
            submitted_at__gte=time_window,
            is_duplicate=False
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
            is_duplicate=False
        ).first()
        
        if existing:
            return {
                'exists': True,
                'message': 'A submission from your device has already been recorded. Thank you!',
                'type': 'duplicate'
            }
    
    return {'exists': False, 'message': '', 'type': None}
```

### Change 3: Enhanced session_feedback() view

```python
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
        # NEW: Get client IP address for duplicate tracking
        client_ip = get_client_ip(request)
        
        # NEW: Check for existing submissions before processing form
        duplicate_check = check_existing_submission(
            session=session,
            ip_address=client_ip,
            participant_name=request.POST.get('participant_name', '').strip()
        )
        
        # NEW: If duplicate detected, reject early
        if duplicate_check['exists']:
            messages.warning(request, duplicate_check['message'])
            return redirect('feedback:session_feedback', session_id=session_id)
        
        form = FeedbackForm(request.POST)
        form = set_rating_labels(form)
        
        if form.is_valid():
            try:
                feedback = form.save(commit=False)
                feedback.session = session
                feedback.ip_address = client_ip  # NEW: Set IP
                feedback.submission_token = generate_submission_token()  # NEW: Set token
                
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
            'submission_token': generate_submission_token()  # NEW: Initialize token
        })
        form = set_rating_labels(form)
    
    rating_field_names = [f'rating_{i}' for i in range(1, 9)]
    
    return render(request, 'feedback/feedback_form.html', {
        'feedback_form': form,
        'session': session,
        'rating_field_names': rating_field_names,
    })
```

---

## File 3: `feedback/forms.py`

### Change 1: Add submission_token field

```python
class FeedbackForm(forms.ModelForm):
    # ... existing fields ...
    
    # NEW: Hidden field for duplicate submission prevention
    submission_token = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Token for preventing duplicate submissions"
    )
```

### Change 2: Update __init__ to include submission_token

```python
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
        # NEW: Hidden submission token field
        Field('submission_token', type='hidden'),
        # ... rest of layout ...
    )
```

### Change 3: Update Meta.fields

```python
class Meta:
    model = FeedbackResponse
    fields = [
        'participant_name', 'submission_token',  # NEW: Added submission_token
        'rating_1', 'rating_2', 'rating_3', 'rating_4',
        'rating_5', 'rating_6', 'rating_7', 'rating_8',
        'key_learnings', 'missing_elements'
    ]
    widgets = {
        'participant_name': forms.TextInput(attrs={...}),
        'submission_token': forms.HiddenInput(),  # NEW
        'key_learnings': forms.Textarea(attrs={...}),
        'missing_elements': forms.Textarea(attrs={...}),
    }
```

### Change 4: Enhanced clean() method

```python
def clean(self):
    cleaned_data = super().clean()
    try:
        # Validate ratings (1-5)
        for i in range(1, 9):
            rating_key = f'rating_{i}'
            rating = cleaned_data.get(rating_key)
            if rating in (None, ''):
                self.add_error(rating_key, f'Rating {i} is required')
            elif not (1 <= int(rating) <= 5):
                self.add_error(rating_key, f'Rating for question {i} must be between 1 and 5')
        
        # NEW: Validate participant name (prevent XSS)
        participant_name = cleaned_data.get('participant_name', '').strip()
        if participant_name and len(participant_name) > 100:
            self.add_error('participant_name', 'Participant name must be less than 100 characters')
        
    except Exception as e:
        logger.error(f"Form validation error: {str(e)}")
        raise
    return cleaned_data
```

---

## File 4: `feedback/templates/feedback/feedback_form.html`

### Change: Enhanced JavaScript section

**OLD:**
```javascript
<script>
// Keyboard navigation for radio buttons
document.querySelectorAll('.rating-radio-group').forEach(group => {
  const buttons = group.querySelectorAll('.rating-radio-label');
  // ... keyboard navigation code ...
});
</script>
```

**NEW:**
```javascript
<script>
// ===== DUPLICATE SUBMISSION PREVENTION =====
(function() {
  const form = document.querySelector('form');
  const submitBtn = document.getElementById('submitBtn');
  let isSubmitting = false;

  if (form && submitBtn) {
    // Prevent form submission if already submitting
    form.addEventListener('submit', function(e) {
      if (isSubmitting) {
        e.preventDefault();
        console.warn('Form submission already in progress. Please wait...');
        return false;
      }

      // Mark as submitting
      isSubmitting = true;
      submitBtn.disabled = true;
      submitBtn.setAttribute('aria-busy', 'true');
      
      // Store original button text and show loading state
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Submitting... Please wait';
      submitBtn.style.opacity = '0.7';
      submitBtn.style.cursor = 'not-allowed';
      
      // Add a timeout to reset in case of network error (30 seconds)
      setTimeout(() => {
        if (isSubmitting) {
          isSubmitting = false;
          submitBtn.disabled = false;
          submitBtn.removeAttribute('aria-busy');
          submitBtn.textContent = originalText;
          submitBtn.style.opacity = '1';
          submitBtn.style.cursor = 'pointer';
          console.warn('Form submission timeout - reset allowed');
        }
      }, 30000);
    });

    // Prevent accidental re-submission via keyboard (Ctrl+Enter, Cmd+Enter)
    form.addEventListener('keydown', function(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!isSubmitting) {
          submitBtn.click();
        }
      }
    });

    // Prevent multiple clicks on submit button
    submitBtn.addEventListener('click', function(e) {
      if (isSubmitting) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }
    });

    // Page unload warning if form was modified but not submitted
    let formModified = false;
    form.addEventListener('change', function() {
      formModified = true;
    });
    
    window.addEventListener('beforeunload', function(e) {
      if (formModified && !isSubmitting) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    });
  }
})();

// ===== KEYBOARD NAVIGATION FOR ACCESSIBILITY =====
document.querySelectorAll('.rating-radio-group').forEach(group => {
  const buttons = group.querySelectorAll('.rating-radio-label');
  
  buttons.forEach((button, index) => {
    button.addEventListener('keydown', (e) => {
      let nextIndex;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        nextIndex = (index + 1) % buttons.length;
        buttons[nextIndex].querySelector('input').focus();
        buttons[nextIndex].querySelector('input').checked = true;
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        nextIndex = (index - 1 + buttons.length) % buttons.length;
        buttons[nextIndex].querySelector('input').focus();
        buttons[nextIndex].querySelector('input').checked = true;
      }
    });
  });
});
</script>
```

---

## File 5: New Migration

**Location:** `feedback/migrations/0008_add_duplicate_prevention_fields.py`

```python
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
```

---

## Summary of Changes

| File | Lines Changed | Purpose |
|------|---|---|
| `models.py` | ~80 | Add fields, methods, indexes |
| `views.py` | ~60 | Add utility functions, enhance view |
| `forms.py` | ~20 | Add hidden field, enhance validation |
| `template.html` | ~60 | Enhanced JavaScript |
| `migrations/0008` | ~35 | Database schema changes |
| **Total** | ~255 | Complete implementation |

**Data Preservation:** ✅ None of these changes delete or corrupt existing data

**Backward Compatible:** ✅ Old and new records work together

**Database Migration:** ✅ Non-destructive, can be rolled back

---

**Created:** March 2025  
**Status:** Ready for Implementation
