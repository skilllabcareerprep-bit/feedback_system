from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'feedback'

urlpatterns = [
    path('', views.home, name='home'),
    path('sessions/', views.public_session_list, name='public_session_list'),
    # Admin-only routes
    path('dashboard/', views.dashboard, name='dashboard'),
    path('sessions/list/', views.session_list, name='session_list'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('sessions/<int:session_id>/report/', views.report_detail, name='report_detail'),
    path('sessions/<int:session_id>/report/generate/', views.generate_report, name='generate_report'),
    path('sessions/<int:session_id>/report/download/', views.download_report, name='download_report'),
    path('sessions/<int:session_id>/email/', views.session_report_email, name='session_report_email'),
    path('trainers/', views.trainer_list, name='trainer_list'),
    path('trainers/create/', views.create_trainer, name='create_trainer'),
    path('trainers/<int:trainer_id>/edit/', views.edit_trainer, name='edit_trainer'),
    path('trainers/<int:trainer_id>/delete/', views.delete_trainer, name='delete_trainer'),
    path('feedback/success/', views.feedback_success, name='feedback_success'),
    path('feedback/summary/', views.feedback_summary, name='feedback_summary'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/change_password.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('sessions/<int:session_id>/toggle/', views.toggle_session_active, name='toggle_session_active'),
    path('sessions/<int:session_id>/download_charts/', views.download_charts, name='download_charts'),
    path('sessions/<int:session_id>/feedback/', views.session_feedback, name='session_feedback'),
    path('form/', views.tabbed_feedback_forms, name='tabbed_feedback_forms'),
    path('feedback/', views.feedback_view, name='feedback_form'),
]
