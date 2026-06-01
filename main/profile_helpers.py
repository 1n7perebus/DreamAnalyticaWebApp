"""Profile, dream ownership, and notification helpers."""

from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from .country_data import COUNTRY_NAME_BY_CODE
from .models import Dreams, DreamComment, Notification, UserProfile

User = get_user_model()


def comment_author_name(user):
    return (user.first_name or '').strip() or user.username


def user_form_identity(request):
    """Default name/email for dream and contact forms when user is signed in."""
    if not request.user.is_authenticated:
        return {}
    name = comment_author_name(request.user)
    email = (request.user.email or '').strip()
    initial = {}
    if name:
        initial['name'] = name
    if email:
        initial['email'] = email
    return initial


MIN_PROFILE_AGE = 13
MAX_PROFILE_AGE = 120
MAX_PROFILE_FIELD_UPDATES = 3
MAX_BIRTH_YEAR_UPDATES = MAX_PROFILE_FIELD_UPDATES


def min_birth_year():
    return timezone.now().year - MAX_PROFILE_AGE


def max_birth_year():
    return timezone.now().year - MIN_PROFILE_AGE


def age_from_birth_year(birth_year, at_date=None):
    """Age at a given date from birth year (calendar-year estimate; month/day not stored)."""
    if not birth_year:
        return None
    try:
        birth_year = int(birth_year)
    except (TypeError, ValueError):
        return None

    if at_date is None:
        at_date = timezone.now().date()
    elif isinstance(at_date, datetime):
        at_date = at_date.date()

    age = at_date.year - birth_year
    if age < MIN_PROFILE_AGE or age > MAX_PROFILE_AGE:
        return None
    return age


def current_age_for_profile(profile):
    if not profile or not profile.birth_year:
        return None
    return age_from_birth_year(profile.birth_year)


def birth_year_choices():
    return [
        (year, str(year))
        for year in range(max_birth_year(), min_birth_year() - 1, -1)
    ]


def profile_updates_remaining(profile, count_field):
    if not profile:
        return MAX_PROFILE_FIELD_UPDATES
    used = getattr(profile, count_field, 0) or 0
    return max(0, MAX_PROFILE_FIELD_UPDATES - used)


def can_update_profile_field(profile, count_field):
    return profile_updates_remaining(profile, count_field) > 0


def birth_year_updates_remaining(profile):
    return profile_updates_remaining(profile, 'birth_year_updates_count')


def can_update_birth_year(profile):
    return can_update_profile_field(profile, 'birth_year_updates_count')


def mbti_updates_remaining(profile):
    return profile_updates_remaining(profile, 'mbti_updates_count')


def can_update_mbti(profile):
    return can_update_profile_field(profile, 'mbti_updates_count')


def mbti_display(code):
    from .models import Dreams

    for value, label in Dreams.MBTI_CHOICES:
        if value == code:
            return label or code
    return code


def enrich_dream_post_data(request, profile=None):
    """Fill POST with account/profile values for hidden consult fields."""
    if not request.user.is_authenticated:
        return request.POST

    post = request.POST.copy()
    identity = user_form_identity(request)
    if identity.get('name'):
        post.setdefault('name', identity['name'])
    if identity.get('email'):
        post.setdefault('email', identity['email'])

    profile = profile or get_or_create_profile(request.user)
    if profile.birth_year:
        age = age_from_birth_year(profile.birth_year)
        if age is not None:
            post.setdefault('age', str(age))
    if profile.mbti_type:
        post.setdefault('mbti_type', profile.mbti_type)
    return post


def enrich_contact_post_data(request):
    if not request.user.is_authenticated:
        return request.POST

    post = request.POST.copy()
    identity = user_form_identity(request)
    if identity.get('name'):
        post.setdefault('name', identity['name'])
    if identity.get('email'):
        post.setdefault('email', identity['email'])
    return post


def consult_form_visibility(request, profile=None):
    """Which consult fields to hide and snapshot values for logged-in users."""
    hide = {
        'name': False,
        'email': False,
        'age': False,
        'mbti': False,
        'gender': False,
    }
    snaps = {}
    identity = {}

    if request.user.is_authenticated:
        identity = user_form_identity(request)
        if identity.get('name'):
            hide['name'] = True
        if identity.get('email'):
            hide['email'] = True
        profile = profile or get_or_create_profile(request.user)
        if profile.birth_year:
            hide['age'] = True
            snaps['age'] = age_from_birth_year(profile.birth_year)
            snaps['birth_year'] = profile.birth_year
        if profile.mbti_type:
            hide['mbti'] = True
            snaps['mbti'] = profile.mbti_type
            snaps['mbti_display'] = mbti_display(profile.mbti_type)

    return {
        'consult_hide': hide,
        'consult_snaps': snaps,
        'consult_identity': identity,
        'consult_display_name': identity.get('name') or (
            comment_author_name(request.user) if request.user.is_authenticated else ''
        ),
        'hide_dreamer_section': hide['name'] and hide['email'],
        'hide_all_profile_fields': hide['age'] and hide['mbti'],
    }


def contact_form_visibility(request):
    hide = {'name': False, 'email': False}
    identity = {}
    if request.user.is_authenticated:
        identity = user_form_identity(request)
        if identity.get('name'):
            hide['name'] = True
        if identity.get('email'):
            hide['email'] = True
    return {
        'contact_hide': hide,
        'contact_identity': identity,
        'contact_display_name': identity.get('name') or (
            comment_author_name(request.user) if request.user.is_authenticated else ''
        ),
        'hide_contact_identity': hide['name'] and hide['email'],
    }


def apply_profile_to_dream_post(request, dream_post, profile):
    """Ensure dream row gets profile snapshots after form validation."""
    if not request.user.is_authenticated:
        return

    identity = user_form_identity(request)
    if not (dream_post.name or '').strip() and identity.get('name'):
        dream_post.name = identity['name']
    if not (dream_post.email or '').strip() and identity.get('email'):
        dream_post.email = identity['email']
    if profile.birth_year:
        dream_post.age = age_from_birth_year(
            profile.birth_year,
            at_date=timezone.now(),
        )
    if profile.mbti_type:
        dream_post.mbti_type = profile.mbti_type


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def dreams_for_user(user):
    email = (user.email or '').strip()
    filters = Q(posted_by=user)
    if email:
        filters |= Q(email__iexact=email)
    return Dreams.objects.filter(filters).distinct().order_by('-pub')


def unread_notification_count(user):
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(recipient=user, read=False).count()


def mark_notifications_read(user):
    Notification.objects.filter(recipient=user, read=False).update(read=True)


def create_comment_notification(comment):
    dream = comment.dream
    dream_email = (dream.email or '').strip()
    if not dream_email:
        return None

    recipient = User.objects.filter(email__iexact=dream_email).first()
    if not recipient:
        return None
    if comment.user_id and comment.user_id == recipient.id:
        return None

    return Notification.objects.create(
        recipient=recipient,
        comment=comment,
        dream=dream,
    )


def apply_profile_country_to_dreams(user, country_code, country_name):
    email = (user.email or '').strip()
    filters = Q(posted_by=user)
    if email:
        filters |= Q(email__iexact=email)
    Dreams.objects.filter(filters).update(
        country_code=country_code[:2].upper(),
        country_name=country_name[:80],
    )


def resolve_country_from_code(country_code):
    code = (country_code or '').strip().upper()
    name = COUNTRY_NAME_BY_CODE.get(code, '')
    return code, name
