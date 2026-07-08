"""One-off diagnostics for registration email + verification pipeline."""
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django

django.setup()

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import get_connection
from django.core.signing import BadSignature, SignatureExpired
from django.test import RequestFactory

from main.pending_registration import (
    PENDING_REGISTRATION_MAX_AGE,
    create_user_from_pending,
    issue_pending_registration_token,
    load_pending_registration_token,
)
from main.views import _pending_verification_verify_url, send_pending_verification_email
from django.contrib.auth.models import User


def section(title):
    print(f'\n=== {title} ===')


def check_config():
    section('Email configuration')
    checks = {
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
        'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
        'EMAIL_HOST_PASSWORD': 'SET' if settings.EMAIL_HOST_PASSWORD else 'MISSING',
    }
    for k, v in checks.items():
        print(f'  {k}: {v}')
    return bool(
        settings.EMAIL_HOST
        and settings.EMAIL_HOST_USER
        and settings.EMAIL_HOST_PASSWORD
        and settings.DEFAULT_FROM_EMAIL
    )


def test_smtp():
    section('Brevo SMTP connection')
    try:
        conn = get_connection()
        conn.open()
        conn.close()
        print('  OK: SMTP connection opened and closed successfully')
        return True
    except Exception as exc:
        print(f'  FAIL: {exc}')
        return False


def test_token_roundtrip():
    section('Verification token round-trip')
    payload = {
        'email': 'pipeline-test@example.com',
        'display_name': 'Pipeline Test',
        'password': make_password('test-pass-123'),
        'birth_year': 1990,
        'mbti_type': 'INFP',
        'country_code': 'US',
    }
    token = issue_pending_registration_token(payload)
    loaded = load_pending_registration_token(token)
    assert loaded['email'] == payload['email']
    print(f'  OK: token length={len(token)} chars, payload verified')

    factory = RequestFactory()
    request = factory.get('/', HTTP_HOST='dreamanalytica.com', secure=True)
    verify_url = _pending_verification_verify_url(request, token)
    print(f'  Sample verify URL host: www.dreamanalytica.com (canonical)')
    print(f'  URL starts with: {verify_url[:80]}...')
    if '/verify-email/?t=' not in verify_url:
        print('  FAIL: URL format unexpected')
        return False
    if not verify_url.startswith('https://www.dreamanalytica.com/verify-email/'):
        print('  FAIL: expected https://www.dreamanalytica.com/verify-email/ prefix')
        return False
    return True


def test_send_email(dry_run=True, to_email=None):
    section('Send test verification email')
    if dry_run:
        print('  SKIP: pass --send to deliver a real test email')
        return None

    to = to_email or os.environ.get('TEST_EMAIL_TO')
    if not to:
        print('  SKIP: set TEST_EMAIL_TO or pass --to=email@example.com')
        return None

    payload = {
        'email': to,
        'display_name': 'Pipeline Test',
        'password': make_password('unused'),
        'birth_year': 1990,
        'mbti_type': 'INFP',
        'country_code': 'US',
    }
    token = issue_pending_registration_token(payload)
    factory = RequestFactory()
    request = factory.get('/', HTTP_HOST='dreamanalytica.com', secure=True)
    try:
        send_pending_verification_email(request, payload, token)
        print(f'  OK: verification email sent to {to}')
        print(f'  Link: {_pending_verification_verify_url(request, token)[:100]}...')
        return True
    except Exception as exc:
        print(f'  FAIL: {exc}')
        return False


def test_user_creation_rollback():
    section('User creation from pending payload (DB test)')
    email = 'pipeline-test-delete-me@example.com'
    User.objects.filter(email=email).delete()
    payload = {
        'email': email,
        'display_name': 'Pipeline Test',
        'password': make_password('test-pass-123'),
        'birth_year': 1990,
        'mbti_type': 'INFP',
        'country_code': 'US',
    }
    try:
        user = create_user_from_pending(payload)
        print(f'  OK: created user id={user.pk}, username={user.username}')
        user.delete()
        print('  OK: cleaned up test user')
        return True
    except Exception as exc:
        print(f'  FAIL: {exc}')
        User.objects.filter(email=email).delete()
        return False


def main():
    send = '--send' in sys.argv
    to_email = None
    for arg in sys.argv[1:]:
        if arg.startswith('--to='):
            to_email = arg.split('=', 1)[1]

    ok = True
    ok &= check_config()
    ok &= test_smtp()
    ok &= test_token_roundtrip()
    result = test_send_email(dry_run=not send, to_email=to_email)
    if result is False:
        ok = False
    ok &= test_user_creation_rollback()

    section('Summary')
    if ok:
        print('  All automated checks passed.')
    else:
        print('  One or more checks FAILED.')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
