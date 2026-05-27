"""Aggregate wall-of-dreams metrics for tabbed analytics UI."""
from django.db.models import Count, Q

# Approximate country centroids (lat, lon) → equirectangular map coords in JS
COUNTRY_LATLON = {
    'AD': (42.55, 1.60), 'AE': (23.42, 53.85), 'AR': (-38.42, -63.62),
    'AT': (47.52, 14.55), 'AU': (-25.27, 133.78), 'BE': (50.50, 4.47),
    'BG': (42.73, 25.49), 'BR': (-14.24, -51.93), 'CA': (56.13, -106.35),
    'CH': (46.82, 8.23), 'CL': (-35.68, -71.54), 'CN': (35.86, 104.20),
    'CO': (4.57, -74.30), 'CZ': (49.82, 15.47), 'DE': (51.17, 10.45),
    'DK': (56.26, 9.50), 'EG': (26.82, 30.80), 'ES': (40.46, -3.75),
    'FI': (61.92, 25.75), 'FR': (46.23, 2.21), 'GB': (55.38, -3.44),
    'GR': (39.07, 21.82), 'HK': (22.40, 114.11), 'HR': (45.10, 15.20),
    'HU': (47.16, 19.50), 'ID': (-0.79, 113.92), 'IE': (53.41, -8.24),
    'IL': (31.05, 34.85), 'IN': (20.59, 78.96), 'IR': (32.43, 53.69),
    'IT': (41.87, 12.57), 'JP': (36.20, 138.25), 'KE': (-0.02, 37.91),
    'KR': (35.91, 127.77), 'MX': (23.63, -102.55), 'MY': (4.21, 101.98),
    'NG': (9.08, 8.68), 'NL': (52.13, 5.29), 'NO': (60.47, 8.47),
    'NZ': (-40.90, 174.89), 'PE': (-9.19, -75.02), 'PH': (12.88, 121.77),
    'PK': (30.38, 69.35), 'PL': (51.92, 19.15), 'PT': (39.40, -8.22),
    'RO': (45.94, 24.97), 'RS': (44.02, 21.01), 'RU': (61.52, 105.32),
    'SA': (23.89, 45.08), 'SE': (60.13, 18.64), 'SG': (1.35, 103.82),
    'TH': (15.87, 100.99), 'TR': (38.96, 35.24), 'TW': (23.70, 120.96),
    'UA': (48.38, 31.17), 'US': (37.09, -95.71), 'VE': (6.42, -66.59),
    'VN': (14.06, 108.28), 'ZA': (-30.56, 22.94),
}

AGE_BUCKETS = (
    ('13–17', 13, 17),
    ('18–24', 18, 24),
    ('25–34', 25, 34),
    ('35–44', 35, 44),
    ('45–54', 45, 54),
    ('55–64', 55, 64),
    ('65+', 65, 120),
)


def _pct(count, total):
    return round((count / total) * 100, 1) if total else 0.0


def build_mbti_gender_stats(active_dreams, dream_count):
    mbti_stats_qs = (
        active_dreams.exclude(mbti_type='')
        .values('mbti_type')
        .annotate(
            total=Count('id'),
            male=Count('id', filter=Q(gender='Male')),
            female=Count('id', filter=Q(gender='Female')),
        )
        .order_by('-total', 'mbti_type')
    )
    rows = []
    if not dream_count:
        return rows
    for row in mbti_stats_qs:
        type_count = row['total']
        male_count = row['male']
        female_count = row['female']
        unknown_count = max(0, type_count - male_count - female_count)
        rows.append({
            'mbti_type': row['mbti_type'],
            'total_pct': _pct(type_count, dream_count),
            'count': type_count,
            'male_pct_wall': _pct(male_count, dream_count),
            'female_pct_wall': _pct(female_count, dream_count),
            'unknown_pct_wall': _pct(unknown_count, dream_count),
            'male_pct_type': _pct(male_count, type_count),
            'female_pct_type': _pct(female_count, type_count),
            'male_count': male_count,
            'female_count': female_count,
            'unknown_count': unknown_count,
        })
    return rows


def build_age_stats(active_dreams, dream_count):
    with_age = active_dreams.filter(age__isnull=False)
    age_total = with_age.count()
    if not age_total:
        return [], 0
    max_count = 0
    buckets = []
    for label, lo, hi in AGE_BUCKETS:
        count = with_age.filter(age__gte=lo, age__lte=hi).count()
        max_count = max(max_count, count)
        buckets.append({
            'label': label,
            'count': count,
            'pct': _pct(count, age_total),
            'pct_wall': _pct(count, dream_count),
        })
    for b in buckets:
        b['bar_pct'] = round((b['count'] / max_count) * 100, 1) if max_count else 0
    return buckets, age_total


def build_gender_pie(active_dreams, dream_count):
    male = active_dreams.filter(gender='Male').count()
    female = active_dreams.filter(gender='Female').count()
    known = male + female
    if not known:
        return None
    other = max(0, dream_count - known)
    male_pct = _pct(male, known)
    female_pct = _pct(female, known)
    return {
        'male_count': male,
        'female_count': female,
        'other_count': other,
        'known_total': known,
        'male_pct': male_pct,
        'female_pct': female_pct,
        'male_end': male_pct,
        'female_end': round(male_pct + female_pct, 1),
    }


def build_country_map(active_dreams, dream_count):
    qs = (
        active_dreams.exclude(country_code='')
        .values('country_code', 'country_name')
        .annotate(count=Count('id'))
        .order_by('-count', 'country_name')
    )
    if not dream_count:
        return [], 0
    geo_total = sum(row['count'] for row in qs)
    if not geo_total:
        return [], 0
    max_count = qs[0]['count'] if qs else 1
    markers = []
    for row in qs:
        code = row['country_code']
        latlon = COUNTRY_LATLON.get(code)
        entry = {
            'code': code,
            'name': row['country_name'] or code,
            'count': row['count'],
            'pct': _pct(row['count'], geo_total),
            'pct_wall': _pct(row['count'], dream_count),
            'size': max(6, min(28, round(6 + (row['count'] / max_count) * 22))),
        }
        if latlon:
            lat, lon = latlon
            entry['x'] = round((lon + 180) / 360 * 960, 1)
            entry['y'] = round((90 - lat) / 180 * 480, 1)
        markers.append(entry)
    return markers, geo_total


def build_wall_analytics(active_dreams, dream_count):
    mbti = build_mbti_gender_stats(active_dreams, dream_count)
    age_buckets, age_total = build_age_stats(active_dreams, dream_count)
    gender_pie = build_gender_pie(active_dreams, dream_count)
    country_markers, geo_total = build_country_map(active_dreams, dream_count)
    return {
        'has_wall_analytics': dream_count > 0,
        'mbti_gender_stats': mbti,
        'age_stats': age_buckets,
        'age_total': age_total,
        'gender_pie': gender_pie,
        'country_markers': country_markers,
        'geo_total': geo_total,
    }
