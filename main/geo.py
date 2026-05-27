"""IP geolocation helpers for dream submissions (server-side only)."""
import json
import os
import urllib.error
import urllib.request

GEO_FIELD_NAMES = (
    'country_code',
    'country_name',
    'region',
    'city',
    'geo_timezone',
)


def _empty_geo():
    return {name: '' for name in GEO_FIELD_NAMES}


def _is_private_ip(ip_address):
    ip = (ip_address or '').strip()
    if not ip or ip == '::1':
        return True
    if ip.startswith('127.'):
        return True
    if ip.startswith('10.'):
        return True
    if ip.startswith('192.168.') or ip.startswith('169.254.'):
        return True
    if ip.startswith('172.'):
        parts = ip.split('.')
        if len(parts) >= 2:
            try:
                if 16 <= int(parts[1]) <= 31:
                    return True
            except ValueError:
                pass
    return False


def get_client_ip(request):
    """Best-effort client IP behind proxies (e.g. PythonAnywhere, Cloudflare)."""
    for header in (
        'HTTP_CF_CONNECTING_IP',
        'HTTP_X_REAL_IP',
        'HTTP_X_FORWARDED_FOR',
    ):
        value = request.META.get(header)
        if not value:
            continue
        candidate = value.split(',')[0].strip()
        if candidate and not _is_private_ip(candidate):
            return candidate
    return (request.META.get('REMOTE_ADDR') or '').strip()


_GEO_API_FIELDS = 'status,country,countryCode,regionName,city,timezone'


def _parse_geo_response(data):
    if not isinstance(data, dict) or data.get('status') != 'success':
        return _empty_geo()
    return {
        'country_code': (data.get('countryCode') or '')[:2].upper(),
        'country_name': (data.get('country') or '')[:80],
        'region': (data.get('regionName') or '')[:100],
        'city': (data.get('city') or '')[:100],
        'geo_timezone': (data.get('timezone') or '')[:64],
    }


def _fetch_geo_url(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return json.loads(response.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def lookup_geo_from_ip(ip_address):
    """
    Resolve country/region/city from IP via ip-api.com (no API key).
    Returns a dict of model field names or empty strings on failure.
    """
    if not ip_address or _is_private_ip(ip_address):
        return _empty_geo()

    url = f'http://ip-api.com/json/{ip_address.strip()}?fields={_GEO_API_FIELDS}'
    data = _fetch_geo_url(url)
    return _parse_geo_response(data) if data is not None else _empty_geo()


def lookup_geo_for_egress():
    """Dev fallback: geo for this server's public IP when the client is localhost."""
    url = f'http://ip-api.com/json/?fields={_GEO_API_FIELDS}'
    data = _fetch_geo_url(url)
    return _parse_geo_response(data) if data is not None else _empty_geo()


def apply_geo_to_dream(dream, ip_address):
    """Write geolocation fields onto a Dreams instance (unsaved)."""
    from django.conf import settings

    override = os.environ.get('GEO_DEV_OVERRIDE_IP') or getattr(settings, 'GEO_DEV_OVERRIDE_IP', None)
    if override:
        geo = lookup_geo_from_ip(str(override).strip())
    elif _is_private_ip(ip_address):
        if settings.DEBUG:
            geo = lookup_geo_for_egress()
        else:
            geo = _empty_geo()
    else:
        geo = lookup_geo_from_ip(ip_address)

    for field in GEO_FIELD_NAMES:
        setattr(dream, field, geo.get(field, ''))
