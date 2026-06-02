from django.urls import path, re_path
from django.views.static import serve
from django.conf import settings
from django.contrib.auth import views as auth_views
from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path('dreams/', views.dreams, name='dreams'),
    path('consult/', views.consult, name='consult'),
    path('contact/', views.contact, name='contact'),
    path('app/', views.app, name='app'),
    path("about/", views.about, name="about"),
    path("error/", views.error, name="error"),
    path('dreams/<uuid:dream_id>/', views.dreams, name='specific_dream'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.txt',
            html_email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('profile/', views.profile_view, name='profile'),
    path('profile/contact-reply/', views.admin_contact_reply, name='admin_contact_reply'),
    path('notifications/<int:notification_id>/open/', views.open_notification, name='open_notification'),
    path('google/auth/callback/', views.google_auth_callback, name='google_auth_callback'),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
]