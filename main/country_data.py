"""ISO 3166-1 alpha-2 codes and display names for profile country selection."""

import json
from pathlib import Path

_COUNTRIES_JSON = (
    Path(__file__).resolve().parent / 'static' / 'main' / 'json' / 'countries.json'
)


def _load_country_choices():
    data = json.loads(_COUNTRIES_JSON.read_text(encoding='utf-8'))
    return sorted(data.items(), key=lambda item: item[1].casefold())


COUNTRY_CHOICES = _load_country_choices()
COUNTRY_NAME_BY_CODE = dict(COUNTRY_CHOICES)
