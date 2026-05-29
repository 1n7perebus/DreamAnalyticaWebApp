"""Parse and normalize dream symbol tags for consistent analytics."""
import re

MAX_SYMBOL_TAGS = 5
MIN_SYMBOL_TAGS = 1
MAX_SYMBOL_LENGTH = 40
MIN_SYMBOL_LENGTH = 2

# Letters, numbers, spaces, hyphen, apostrophe (e.g. mother's house -> split tags by comma only)
SYMBOL_CHAR_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\s\-']*$")


def normalize_symbol_name(raw: str) -> str:
    """Canonical display form: trim, collapse spaces, title case (Snake, Flying, Mother)."""
    if not raw:
        return ''
    collapsed = ' '.join(str(raw).strip().split())
    if not collapsed:
        return ''
    return collapsed.title()


def parse_symbol_tags(raw: str) -> list[str]:
    """
    Split comma/semicolon-separated input into unique canonical symbol names.
    Case-insensitive dedupe: snake + Snake -> one 'Snake'.
    """
    if not raw or not str(raw).strip():
        return []

    parts = re.split(r'[,;\n]+', str(raw))
    seen_lower = set()
    out = []

    for part in parts:
        name = normalize_symbol_name(part)
        if not name:
            continue
        if len(name) < MIN_SYMBOL_LENGTH:
            raise ValueError(f'Each symbol needs at least {MIN_SYMBOL_LENGTH} characters (got "{name}").')
        if len(name) > MAX_SYMBOL_LENGTH:
            raise ValueError(f'Each symbol must be {MAX_SYMBOL_LENGTH} characters or fewer.')
        if not SYMBOL_CHAR_RE.match(name):
            raise ValueError(
                f'"{name}" contains invalid characters. Use letters, numbers, spaces, or hyphens only.'
            )
        key = name.lower()
        if key in seen_lower:
            continue
        seen_lower.add(key)
        out.append(name)
        if len(out) > MAX_SYMBOL_TAGS:
            raise ValueError(f'Please enter at most {MAX_SYMBOL_TAGS} symbols.')

    if len(out) < MIN_SYMBOL_TAGS:
        raise ValueError(f'Add at least {MIN_SYMBOL_TAGS} dream symbol.')

    return out


def resolve_symbol_tags(names: list[str]):
    """Return DreamSymbol rows for canonical names (case-insensitive get_or_create)."""
    from .models import DreamSymbol

    objs = []
    for name in names:
        name = normalize_symbol_name(name)
        if not name:
            continue
        existing = DreamSymbol.objects.filter(name__iexact=name).first()
        if existing:
            objs.append(existing)
        else:
            objs.append(DreamSymbol.objects.create(name=name))
    return objs
