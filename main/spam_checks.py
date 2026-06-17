"""Registration anti-spam helpers."""

import re
from datetime import timedelta

from django.utils import timezone

from .models import RegistrationAttempt

# Common disposable / throwaway inbox domains (lowercase).
DISPOSABLE_EMAIL_DOMAINS = frozenset({
    '10minutemail.com',
    '10minutemail.net',
    'dispostable.com',
    'dropmail.me',
    'fakeinbox.com',
    'getairmail.com',
    'getnada.com',
    'guerrillamail.com',
    'guerrillamail.net',
    'guerrillamail.org',
    'maildrop.cc',
    'mailinator.com',
    'mailinator.net',
    'mailnesia.com',
    'mailcatch.com',
    'mintemail.com',
    'moakt.com',
    'mytemp.email',
    'sharklasers.com',
    'spam4.me',
    'temp-mail.org',
    'tempmail.com',
    'tempmail.net',
    'tempmailo.com',
    'throwaway.email',
    'trashmail.com',
    'trashmail.net',
    'yopmail.com',
    'yopmail.fr',
    'yopmail.net',
})

REGISTRATION_MAX_ATTEMPTS_PER_HOUR = 5
REGISTRATION_MAX_ATTEMPTS_PER_DAY = 15
REGISTRATION_ATTEMPT_RETENTION_DAYS = 7


def email_domain(email):
    return (email or '').rsplit('@', 1)[-1].strip().lower()


def is_disposable_email(email):
    domain = email_domain(email)
    if not domain:
        return False
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return True
    # mailinator-style subdomains
    for blocked in DISPOSABLE_EMAIL_DOMAINS:
        if domain.endswith('.' + blocked):
            return True
    return False


def looks_like_bot_display_name(name):
    """Heuristic for random gibberish bot names (e.g. HywQdjXpCgcLvNZrA)."""
    text = (name or '').strip()
    if len(text) < 10 or ' ' in text:
        return False
    if not text.isalpha():
        return False
    if not (any(c.isupper() for c in text) and any(c.islower() for c in text)):
        return False
    vowels = len(re.findall(r'[aeiouAEIOU]', text))
    ratio = vowels / len(text)
    if len(text) >= 12 and ratio < 0.2:
        return True
    if len(text) >= 16 and ratio < 0.3:
        return True
    return False


def _prune_old_registration_attempts():
    cutoff = timezone.now() - timedelta(days=REGISTRATION_ATTEMPT_RETENTION_DAYS)
    RegistrationAttempt.objects.filter(created_at__lt=cutoff).delete()


def registration_rate_limited(ip_address):
    if not (ip_address or '').strip():
        return False

    _prune_old_registration_attempts()
    now = timezone.now()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    recent_hour = RegistrationAttempt.objects.filter(
        ip_address=ip_address,
        created_at__gte=hour_ago,
    ).count()
    if recent_hour >= REGISTRATION_MAX_ATTEMPTS_PER_HOUR:
        return True

    recent_day = RegistrationAttempt.objects.filter(
        ip_address=ip_address,
        created_at__gte=day_ago,
    ).count()
    return recent_day >= REGISTRATION_MAX_ATTEMPTS_PER_DAY


def record_registration_attempt(ip_address, email=''):
    if not (ip_address or '').strip():
        return
    RegistrationAttempt.objects.create(
        ip_address=ip_address.strip()[:45],
        email=(email or '').strip().lower()[:254],
    )
