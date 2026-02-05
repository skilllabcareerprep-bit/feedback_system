from django.contrib import admin
from .models import Trainer, TrainingSession, FeedbackResponse, FeedbackReport

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'specialization', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'specialization']
    search_fields = ['name', 'email']
    list_editable = ['is_active']

@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['session_title', 'trainer', 'date', 'institution', 'audience', 'get_feedback_count', 'is_active']
    list_filter = ['trainer', 'date', 'is_active']
    search_fields = ['session_title', 'trainer__name', 'institution', 'audience']
    list_editable = ['is_active']
    date_hierarchy = 'date'

@admin.register(FeedbackResponse)
class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ['session', 'participant_name', 'get_average_rating', 'submitted_at']
    list_filter = ['session__trainer', 'submitted_at']
    search_fields = ['session__session_title', 'participant_name']
    readonly_fields = ['submitted_at', 'ip_address']

@admin.register(FeedbackReport)
class FeedbackReportAdmin(admin.ModelAdmin):
    list_display = ['session', 'generated_at', 'email_sent', 'email_sent_at']
    list_filter = ['email_sent', 'generated_at']
    readonly_fields = ['generated_at'] 
