"""Cloudflare Turnstile verification for bot protection."""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


def verify_turnstile(token, remote_ip=None):
    secret = getattr(settings, 'TURNSTILE_SECRET_KEY', '') or ''
    if not secret:
        return True

    if not (token or '').strip():
        return False

    payload = urllib.parse.urlencode({
        'secret': secret,
        'response': token.strip(),
        'remoteip': (remote_ip or '').strip(),
    }).encode()

    request = urllib.request.Request(
        TURNSTILE_VERIFY_URL,
        data=payload,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        logger.exception('Turnstile verification request failed')
        return False

    if not body.get('success'):
        logger.info('Turnstile rejected token: %s', body.get('error-codes'))
    return bool(body.get('success'))
