from collections import Counter
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import timedelta
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator


from django.db.models import *
from .forms import *
from .models import *
from .geo import apply_geo_to_dream, get_client_ip
from .dream_symbols import resolve_symbol_tags
from .profile_helpers import (
    age_from_birth_year,
    apply_profile_country_to_dreams,
    apply_profile_to_dream_post,
    birth_year_updates_remaining,
    can_update_birth_year,
    can_update_mbti,
    comment_author_name,
    consult_form_visibility,
    contact_form_visibility,
    create_comment_notification,
    current_age_for_profile,
    dreams_for_user,
    enrich_contact_post_data,
    enrich_dream_post_data,
    get_or_create_profile,
    mbti_display,
    mbti_updates_remaining,
    resolve_country_from_code,
    user_form_identity,
)
# Checklist
# Add Sections
# Advertising Goodgle Adsense 
# Payment Mothod
# Adjust Submission Time


def redirect_after_login(request, user):
    if not (user.first_name or '').strip():
        return reverse('main:login') + '?setup=1'
    return request.session.pop('next', reverse('main:index'))


def delete_duplicates(dream_post):
    duplicates = Dreams.objects.filter(
        title=dream_post.title
    ) | Dreams.objects.filter(
        dream=dream_post.dream
    )

    # If duplicates exist, delete them
    if duplicates.exists():
        duplicates.delete()

#@login_required
#@never_cache
def index(request):
    return render(request, "dreamapp/index.html", context={})


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.is_active = False
            new_user.save()
            form.save_profile(new_user)
            send_verification_email(request, new_user)
            messages.success(request, 'Account created. Check your email to verify your account before signing in.')
            return redirect('main:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'dreamapp/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        if request.method == 'POST' and 'display_name' in request.POST:
            name = request.POST.get('display_name', '').strip()[:50]
            if name:
                request.user.first_name = name
                request.user.save(update_fields=['first_name'])
                messages.success(request, f'Welcome, {name}!')
                return redirect(request.session.pop('next', reverse('main:index')))
            messages.error(request, 'Please enter a display name.')
        if not (request.user.first_name or '').strip() or request.GET.get('setup') == '1':
            return render(request, 'dreamapp/login.html', {
                'profile_setup': True,
                'google_client_id': settings.GOOGLE_CLIENT_ID,
            })
        return redirect('main:index')

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                messages.error(request, 'Your account is not verified yet. Please check your email for the verification link.')
                return render(request, 'dreamapp/login.html', {
                    'google_client_id': settings.GOOGLE_CLIENT_ID,
                    'google_login_uri': request.build_absolute_uri(reverse('main:google_auth_callback')),
                })
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect(redirect_after_login(request, user))
            messages.error(request, 'Invalid email or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')

    return render(request, 'dreamapp/login.html', {
        'google_client_id': settings.GOOGLE_CLIENT_ID,
        'google_login_uri': request.build_absolute_uri(reverse('main:google_auth_callback')),
    })


def logout_view(request):
    logout(request)
    return redirect('main:login')


def send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse('main:verify_email', kwargs={'uidb64': uid, 'token': token})
    )
    context = {
        'user': user,
        'verify_url': verify_url,
    }
    html_message = render_to_string('dreamapp/email_templates/account_verification.html', context)
    plain_message = strip_tags(html_message)
    email = EmailMultiAlternatives(
        subject='Verify your Dream Analytica account',
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_message, 'text/html')
    email.send(fail_silently=False)


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        messages.success(request, 'Email verified. You can now sign in.')
        return redirect('main:login')

    messages.error(request, 'Verification link is invalid or has expired.')
    return redirect('main:login')


def _admin_only_or_redirect(request):
    if request.user.is_staff or request.user.is_superuser:
        return None
    messages.error(request, 'Admin access required.')
    return redirect('main:profile')


@login_required
def profile_view(request):
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'set_country' and not profile.country_locked:
            country_form = ProfileCountryForm(request.POST)
            if country_form.is_valid():
                code, name = resolve_country_from_code(
                    country_form.cleaned_data['country_code'],
                )
                if code and name:
                    profile.country_code = code
                    profile.country_name = name
                    profile.country_locked = True
                    profile.save()
                    apply_profile_country_to_dreams(request.user, code, name)
                    messages.success(
                        request,
                        'Country saved. All your dreams now show this country on the wall.',
                    )
                else:
                    messages.error(request, 'Please select a valid country.')
            else:
                messages.error(request, 'Please select a country.')
        elif action == 'update_birth_year':
            if not can_update_birth_year(profile):
                messages.error(
                    request,
                    'Birth year can only be set or changed 3 times. Contact support if you need help.',
                )
            else:
                previous_birth_year = profile.birth_year
                birth_year_form = ProfileBirthYearForm(request.POST, instance=profile)
                if birth_year_form.is_valid():
                    new_year = birth_year_form.cleaned_data['birth_year']
                    if new_year != previous_birth_year:
                        profile.birth_year = new_year
                        profile.birth_year_updates_count += 1
                        profile.save(
                            update_fields=['birth_year', 'birth_year_updates_count'],
                        )
                        remaining = birth_year_updates_remaining(profile)
                        if remaining:
                            messages.success(
                                request,
                                f'Birth year saved. You have {remaining} '
                                f'update{"s" if remaining != 1 else ""} left.',
                            )
                        else:
                            messages.success(
                                request,
                                'Birth year saved. No more changes allowed.',
                            )
                    else:
                        messages.info(request, 'Birth year unchanged.')
                else:
                    messages.error(request, 'Please select a valid birth year.')
        elif action == 'update_mbti':
            if not can_update_mbti(profile):
                messages.error(
                    request,
                    'Personality type can only be set or changed 3 times. Contact support if you need help.',
                )
            else:
                previous_mbti = profile.mbti_type
                mbti_form = ProfileMbtiForm(request.POST, instance=profile)
                if mbti_form.is_valid():
                    new_mbti = mbti_form.cleaned_data['mbti_type']
                    if new_mbti != previous_mbti:
                        profile.mbti_type = new_mbti
                        profile.mbti_updates_count += 1
                        profile.save(
                            update_fields=['mbti_type', 'mbti_updates_count'],
                        )
                        remaining = mbti_updates_remaining(profile)
                        if remaining:
                            messages.success(
                                request,
                                f'Personality type saved. You have {remaining} '
                                f'update{"s" if remaining != 1 else ""} left.',
                            )
                        else:
                            messages.success(
                                request,
                                'Personality type saved. No more changes allowed.',
                            )
                    else:
                        messages.info(request, 'Personality type unchanged.')
                else:
                    messages.error(request, 'Please select a valid personality type.')
        elif action == 'mark_all_notifications_read':
            Notification.objects.filter(recipient=request.user, read=False).update(read=True)
            messages.success(request, 'All notifications marked as read.')
        else:
            messages.error(request, 'Could not save profile changes.')
        return redirect('main:profile')

    notif_filter = request.GET.get('notif', 'unread').strip().lower()
    if notif_filter not in {'unread', 'all'}:
        notif_filter = 'unread'

    notifications_qs = (
        Notification.objects.filter(recipient=request.user)
        .select_related('comment', 'dream')
        .order_by('-created_at')
    )
    if notif_filter == 'unread':
        notifications_qs = notifications_qs.filter(read=False)

    notif_paginator = Paginator(notifications_qs, 25)
    notifications_page = notif_paginator.get_page(request.GET.get('np'))

    admin_contacts = None
    if request.user.is_staff or request.user.is_superuser:
        admin_contacts = Contact.objects.order_by('-pub')[:25]

    return render(request, 'dreamapp/profile.html', {
        'profile': profile,
        'display_name': comment_author_name(request.user),
        'user_dreams': dreams_for_user(request.user),
        'notifications': notifications_page,
        'notifications_total_count': notifications_qs.count(),
        'notification_filter': notif_filter,
        'country_form': None if profile.country_locked else ProfileCountryForm(),
        'birth_year_form': ProfileBirthYearForm(instance=profile),
        'mbti_form': ProfileMbtiForm(instance=profile),
        'profile_current_age': current_age_for_profile(profile),
        'profile_mbti_display': mbti_display(profile.mbti_type) if profile.mbti_type else '',
        'birth_year_updates_remaining': birth_year_updates_remaining(profile),
        'mbti_updates_remaining': mbti_updates_remaining(profile),
        'birth_year_form_open': not profile.birth_year,
        'mbti_form_open': not profile.mbti_type,
        'admin_contacts': admin_contacts,
    })


@login_required
def admin_contact_reply(request):
    denied_response = _admin_only_or_redirect(request)
    if denied_response:
        return denied_response

    contact_id = (request.GET.get('contact') or request.POST.get('contact_id') or '').strip()
    contact_item = None
    if contact_id:
        contact_item = Contact.objects.filter(pk=contact_id).first()

    initial = {}
    if contact_item:
        initial['to_email'] = contact_item.email

    if request.method == 'POST':
        form = AdminContactReplyForm(request.POST, initial=initial)
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            message_body = form.cleaned_data['message'].strip()
            recipient_name = ''
            if contact_item and (contact_item.name or '').strip():
                recipient_name = contact_item.name.strip()
            if not recipient_name:
                recipient_name = to_email

            context = {
                'to_email': to_email,
                'recipient_name': recipient_name,
                'message': message_body,
                'admin_name': comment_author_name(request.user),
            }
            html_message = render_to_string(
                'dreamapp/email_templates/admin_contact_reply.html',
                context,
            )
            plain_message = strip_tags(html_message)
            email = EmailMultiAlternatives(
                subject='Dream Analytica — Response to your inquiry',
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            email.attach_alternative(html_message, 'text/html')
            email.send(fail_silently=False)
            messages.success(request, f'Reply sent to {to_email}.')
            return redirect('main:admin_contact_reply')
    else:
        form = AdminContactReplyForm(initial=initial)

    recent_contacts = Contact.objects.order_by('-pub')[:100]
    return render(
        request,
        'dreamapp/admin_contact_reply.html',
        {
            'form': form,
            'contact_item': contact_item,
            'recent_contacts': recent_contacts,
        },
    )


@login_required
def open_notification(request, notification_id):
    note = get_object_or_404(
        Notification.objects.select_related('dream', 'comment'),
        id=notification_id,
        recipient=request.user,
    )
    if not note.read:
        note.read = True
        note.save(update_fields=['read'])
    return redirect(
        reverse('main:specific_dream', kwargs={'dream_id': note.dream_id}) +
        f'#comment-{note.comment_id}'
    )


def _login_user_from_google_token(token):
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError('Google sign-in is not configured')
    idinfo = id_token.verify_oauth2_token(
        token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
    )
    email = idinfo.get('email')
    if not email:
        raise ValueError('Email not provided by Google')
    google_name = (idinfo.get('given_name') or idinfo.get('name') or '').strip()[:50]
    user = User.objects.filter(email=email).first()
    if not user:
        base = email.split('@')[0].replace('.', '')[:20] or 'user'
        username = base
        n = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{n}'
            n += 1
        user = User.objects.create_user(username=username, email=email)
        user.set_unusable_password()
        if google_name:
            user.first_name = google_name
        user.save()
    elif google_name and not (user.first_name or '').strip():
        user.first_name = google_name
        user.save(update_fields=['first_name'])
    return user


@csrf_exempt
@require_POST
def google_auth_callback(request):
    token = request.POST.get('credential') or request.POST.get('code')
    if not token:
        messages.error(request, 'Google sign-in did not return a token.')
        return redirect('main:login')
    try:
        user = _login_user_from_google_token(token)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('main:login')
    login(request, user)
    return redirect(redirect_after_login(request, user))


def consult(request):
    dreams = Dreams.objects.all()
    recent_submission = False

    Dreams.objects.filter(name="AlbertJipix").delete()
    Dreams.objects.filter(title="DON'T MISS OUT: CLAIM YOUR $50,000 WINNI").delete()
        
    if request.method == "POST":
        ip_address = get_client_ip(request)
        recent_submission = Dreams.objects.filter(ip_address=ip_address, submission_time__gte=timezone.now() - timedelta(days=1)).exists()
        
        if recent_submission:
            last_submission_time = Dreams.objects.filter(ip_address=ip_address).latest('submission_time').submission_time
            current_time = timezone.now()
            time_difference = current_time - last_submission_time
            wait_time_seconds = timedelta(days=1).total_seconds() - time_difference.total_seconds()

            hours, remainder = divmod(wait_time_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            wait_message = ""
            if hours >= 1:
                wait_message += f"{int(hours)} hour{'s' if int(hours) > 1 else ''}"
            if minutes >= 1:
                wait_message += f" {int(minutes)} minute{'s' if int(minutes) > 1 else ''}"
            if seconds >= 1:
                wait_message += f" {int(seconds)} second{'s' if int(seconds) > 1 else ''}"

            messages.error(request, f"To prevent spamming, please wait {wait_message} before resubmitting.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        profile = None
        if request.user.is_authenticated:
            profile = get_or_create_profile(request.user)

        dream_form = DreamForm(enrich_dream_post_data(request, profile))
        if dream_form.is_valid() and not recent_submission:
            dream_post = dream_form.save(commit=False)
            dream_post.ip_address = ip_address
            apply_geo_to_dream(dream_post, ip_address)

            if request.user.is_authenticated:
                dream_post.posted_by = request.user
                apply_profile_to_dream_post(request, dream_post, profile)

            delete_duplicates(dream_post)

            sender = dream_post.email
            dream_post.save()
            pending_symbols = getattr(dream_form, '_pending_symbol_names', [])
            if pending_symbols:
                dream_post.symbols.set(resolve_symbol_tags(pending_symbols))
            Dreams.objects.filter(name="AlbertJipix").delete()

            from_email = 'dreamanalytica@outlook.com'
            to_email = 'dreamanalytica08@gmail.com'
            
            subject = "New Dream Submission"
            context = {
                "name": dream_post.name,
                "mbti_type": dream_post.mbti_type,
                "email": dream_post.email,
                "title": dream_post.title,
                "dream": dream_post.dream,
                "scale": dream_post.scale,
                "pub": dream_post.pub,
                "age": dream_post.age,
                "country_name": dream_post.country_name,
                "region": dream_post.region,
                "city": dream_post.city,
            }

            html_message = render_to_string("dreamapp/email_templates/dream_submission.html", context)
            plain_message = strip_tags(html_message)
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=from_email,
                to=[to_email, sender],
            )
            email.attach_alternative(html_message, "text/html")
            #email.send(fail_silently=True)
            
            return HttpResponseRedirect(reverse('main:dreams'))
        else:
            messages.error(request, "Invalid form data. Please check the entered information.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    else:
        dream_form = DreamForm(initial=user_form_identity(request))

    mbti_choices = DreamForm.MBTI_CHOICES
    gender_choices = DreamForm.GENDER_CHOICES
    symbol_suggestions = DreamSymbol.objects.all()[:200]

    profile = None
    if request.user.is_authenticated:
        profile = get_or_create_profile(request.user)

    consult_ctx = consult_form_visibility(request, profile)

    return render(request, "dreamapp/consult.html", {
        "dreams": dreams,
        "dream_form": dream_form,
        "recent_submission": recent_submission,
        "mbti_choices": mbti_choices,
        'gender_choices': gender_choices,
        'symbol_suggestions': symbol_suggestions,
        'user_profile': profile,
        **consult_ctx,
    })



def dreams(request, dream_id=None):
    focus_dream = None
    if dream_id is not None:
        focus_dream = get_object_or_404(Dreams, pk=dream_id)
        if not focus_dream.active:
            messages.info(
                request,
                'This dream is not on the public wall yet.',
            )

    comment_form = CommentForm()
    dreams = Dreams.objects.all()

    avg_result = dreams.filter(active=True).aggregate(Avg('scale'))['scale__avg']
    average_scale = round(avg_result, 2) if avg_result is not None else None

    duplicates = Dreams.objects.values('title', 'dream').annotate(count=Count('id')).filter(count__gt=1)
    for duplicate in duplicates:
        Dreams.objects.filter(
            name=duplicate['name'],
        ).delete() 

    Dreams.objects.filter(name__in=["AlbertJipix", "Davidbiani","Search Engine Index"]).delete()

    if average_scale is not None:
        if average_scale > 3.5:
            health_status = "balanced"
            health_color = "#53FFFB"
        elif average_scale < 2.5:
            health_status = "unbalanced"
            health_color = "#FF007D"
        else:
            health_status = "neutral"
            health_color = "#FFE66D"
    else:
        health_status = "No data available"
        health_color = "#FFE66D"

    if request.method == 'POST':
        if not request.user.is_authenticated:
            # Store the current URL in the session and redirect to login
            request.session['next'] = request.path
            messages.error(request, 'You need to be logged in to comment.')
            return redirect('main:login')

        comment_form = CommentForm(request.POST)

        if comment_form.is_valid():
            dream_id = request.POST.get('dream_id')
            dream_email = request.POST.get('dream_email')
            try:
                if dream_id:
                    dream_instance = get_object_or_404(Dreams, id=dream_id)
                else:
                    dream_instance = get_object_or_404(Dreams, email=dream_email)

                recent_comment = DreamComment.objects.filter(
                    user=request.user,
                    dream=dream_instance,
                    pub__gte=timezone.now() - timedelta(days=1),
                ).exists()

                if recent_comment:
                    messages.error(
                        request,
                        'You can post one comment per dream per day. Try again tomorrow.',
                    )
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                comment = comment_form.save(commit=False)
                comment.dream = dream_instance
                comment.user = request.user
                comment.name = comment_author_name(request.user)
                comment.pub = timezone.now()
                comment.save()
                create_comment_notification(comment)

                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            except Dreams.DoesNotExist:
                messages.error(request, "Dream not found. Please check the email address.")
            except Exception as e:
                print(f"Error: {e}")
                messages.error(request, "An error occurred. Please try again later.")
            
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, "Invalid form data. Please check the entered information.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    active_dreams = Dreams.objects.filter(active=True).prefetch_related('comments').order_by('-pub')
    dreams_with_comments = [
        {'dream': dream, 'comments': dream.comments.all()}
        for dream in active_dreams
    ]

    dream_count = active_dreams.count()

    from .wall_analytics import build_wall_analytics

    analytics = build_wall_analytics(active_dreams, dream_count)

    return render(request, "dreamapp/dreams.html", {
        "dreams_with_comments": dreams_with_comments,
        "dreams": dreams,
        "comment_form": comment_form,
        "average_scale": average_scale,
        "health_status": health_status,
        "health_color": health_color,
        "dream_count": dream_count,
        "focus_dream": focus_dream,
        **analytics,
    })


CONTACT_TOPIC_LABELS = {
    'general': 'General question',
    'dream': 'Dream / analysis',
    'collaboration': 'Collaboration / press',
    'technical': 'Technical / app',
    'other': 'Other',
}


def _contact_topic_prefix(topic_key):
    label = CONTACT_TOPIC_LABELS.get(topic_key, CONTACT_TOPIC_LABELS['general'])
    return f'[Topic: {label}]\n\n'


def contact(request):
    contact_sent = request.session.pop('contact_sent', False)

    if request.method == "POST":
        ip_address = request.META.get('REMOTE_ADDR')
        recent_submission = Contact.objects.filter(
            ip_address=ip_address,
            submission_time__gte=timezone.now() - timedelta(seconds=1),
        ).exists()

        if recent_submission:
            last_submission_time = Contact.objects.filter(
                ip_address=ip_address,
            ).latest('submission_time').submission_time
            time_difference = timezone.now() - last_submission_time
            wait_time_seconds = timedelta(days=1).total_seconds() - time_difference.total_seconds()

            hours, remainder = divmod(wait_time_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            wait_message = ""
            if hours >= 1:
                wait_message += f"{int(hours)} hour{'s' if int(hours) > 1 else ''}"
            if minutes >= 1:
                wait_message += f" {int(minutes)} minute{'s' if int(minutes) > 1 else ''}"
            if seconds >= 1:
                wait_message += f" {int(seconds)} second{'s' if int(seconds) > 1 else ''}"

            messages.error(
                request,
                f"To prevent spamming, please wait {wait_message.strip()} before resubmitting.",
            )
            return redirect('main:contact')

        contact_form = ContactForm(enrich_contact_post_data(request))
        if contact_form.is_valid() and not recent_submission:
            topic_key = request.POST.get('contact_topic', 'general').strip().lower()
            if topic_key not in CONTACT_TOPIC_LABELS:
                topic_key = 'general'

            contact_post = contact_form.save(commit=False)
            contact_post.ip_address = ip_address
            body = (contact_post.desc or '').strip()
            contact_post.desc = _contact_topic_prefix(topic_key) + body
            contact_post.save()

            request.session['contact_sent'] = True
            messages.success(
                request,
                "Message received. We will reply to your email within 24–48 hours.",
            )
            return redirect('main:contact')

        topic_key = request.POST.get('contact_topic', 'general').strip().lower()
        if topic_key not in CONTACT_TOPIC_LABELS:
            topic_key = 'general'
        messages.error(request, "Please fix the highlighted fields below.")
        return render(
            request,
            "dreamapp/contact.html",
            {
                "contact_form": contact_form,
                "contact_sent": False,
                "contact_topic": topic_key,
                **contact_form_visibility(request),
            },
        )

    contact_form = ContactForm(initial=user_form_identity(request))
    return render(
        request,
        "dreamapp/contact.html",
        {
            "contact_form": contact_form,
            "contact_sent": contact_sent,
            "contact_topic": "general",
            **contact_form_visibility(request),
        },
    )



def app(request):
    return render(request, "dreamapp/app.html")

def about(request):
    return render(request, "dreamapp/about.html")

def error(request):
    return render(request, "dreamapp/error.html")
