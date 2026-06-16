"""Signed-token storage for registrations pending email verification."""

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import transaction

from .country_data import COUNTRY_CHOICES
from .forms import unique_username_from_name
from .models import UserProfile

PENDING_REGISTRATION_SALT = 'main.pending-registration'
PENDING_REGISTRATION_MAX_AGE = 60 * 60 * 24  # 24 hours

_signer = TimestampSigner(salt=PENDING_REGISTRATION_SALT)


def build_payload_from_form(form):
    """Build a serializable registration payload from validated form data."""
    return {
        'email': form.cleaned_data['email'],
        'display_name': form.cleaned_data['display_name'].strip()[:50],
        'password': make_password(form.cleaned_data['password']),
        'birth_year': form.cleaned_data['birth_year'],
        'mbti_type': form.cleaned_data['mbti_type'],
        'country_code': form.cleaned_data['country_code'],
    }


def issue_pending_registration_token(payload):
    """Return a fresh signed token (resets the 24-hour expiry clock)."""
    return _signer.sign_object(payload, compress=True)


def load_pending_registration_token(token, *, max_age=PENDING_REGISTRATION_MAX_AGE):
    return _signer.unsign_object(token, max_age=max_age)


def create_user_from_pending(payload):
    """Create an active User and UserProfile from a verified pending payload."""
    email = payload['email']
    display_name = payload['display_name']

    with transaction.atomic():
        user = User(
            email=email,
            first_name=display_name,
            username=unique_username_from_name(display_name, email),
            password=payload['password'],
            is_active=True,
        )
        user.save()

        country_code = payload['country_code']
        UserProfile.objects.create(
            user=user,
            birth_year=payload['birth_year'],
            birth_year_updates_count=1,
            mbti_type=payload['mbti_type'],
            mbti_updates_count=1,
            country_code=country_code,
            country_name=dict(COUNTRY_CHOICES).get(country_code, ''),
            country_locked=True,
        )

    return user
