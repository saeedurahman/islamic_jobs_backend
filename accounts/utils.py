import random
import re

PAKISTANI_PHONE_PATTERN = re.compile(r'^03\d{9}$')


def normalize_phone_number(value: str) -> str:
    """Normalize to 03XXXXXXXXX (11 digits, starts with 0)."""
    normalized = value.strip().replace(' ', '').replace('-', '')
    if normalized.startswith('+92'):
        normalized = '0' + normalized[3:]
    elif normalized.startswith('92') and len(normalized) == 12:
        normalized = '0' + normalized[2:]
    return normalized


def is_valid_pakistani_phone(value: str) -> bool:
    return bool(PAKISTANI_PHONE_PATTERN.match(value))


def generate_username(email: str) -> str:
    """Generate a unique username from the email local part."""
    base = email.split('@')[0]
    base = re.sub(r'[^\w.@+-]', '', base)[:30]
    if not base:
        base = 'user'

    from accounts.models import User

    username = base
    while User.objects.filter(username=username).exists():
        username = f'{base}{random.randint(1000, 9999)}'
    return username
