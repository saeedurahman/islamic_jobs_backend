import secrets

from django.db import transaction
from django.utils.text import slugify

from accounts.models import User
from accounts.utils import generate_username, is_valid_pakistani_phone, normalize_phone_number
from employers.models import Employer
from jobs.models import JobPosting
from profiles.validators import get_location_consistency_errors


INTERNAL_EMAIL_DOMAIN = 'islamicjobz.internal'


def generate_internal_employer_email(organization_name: str) -> str:
    base = slugify(organization_name)[:40] or 'employer'
    for _ in range(20):
        candidate = f'{base}-{secrets.token_hex(4)}@{INTERNAL_EMAIL_DOMAIN}'
        if not User.objects.filter(email__iexact=candidate).exists():
            return candidate
    return f'{base}-{secrets.token_hex(8)}@{INTERNAL_EMAIL_DOMAIN}'


def _normalize_phone(value, field_name):
    if value in (None, ''):
        return value
    normalized = normalize_phone_number(value)
    if not is_valid_pakistani_phone(normalized):
        raise ValueError(
            f'{field_name}: enter a valid Pakistani phone number '
            '(e.g. 03001234567 or +923001234567).'
        )
    return normalized


@transaction.atomic
def create_admin_employer_and_job(*, employer_data, job_data, admin_notes=''):
    whatsapp_number = _normalize_phone(employer_data['whatsapp_number'], 'whatsapp_number')
    contact_phone = _normalize_phone(
        employer_data.get('contact_phone'),
        'contact_phone',
    )

    contact_email = (employer_data.get('contact_email') or '').strip().lower()
    account_email = contact_email or generate_internal_employer_email(
        employer_data['organization_name']
    )
    if User.objects.filter(email__iexact=account_email).exists():
        raise ValueError('A user with this email already exists.')

    if User.objects.filter(phone_number=whatsapp_number).exists():
        raise ValueError('This WhatsApp number is already registered to another account.')

    employer_province = employer_data['province']
    employer_city = employer_data['city']
    employer_district = employer_data.get('district')
    employer_location_errors = get_location_consistency_errors(
        employer_province,
        employer_city,
        district=employer_district,
    )
    if employer_location_errors:
        raise ValueError(employer_location_errors)

    job_province = job_data['province']
    job_city = job_data['city']
    job_district = job_data.get('district')
    job_location_errors = get_location_consistency_errors(
        job_province,
        job_city,
        district=job_district,
    )
    if job_location_errors:
        raise ValueError(job_location_errors)

    salary_min = job_data.get('salary_min')
    salary_max = job_data.get('salary_max')
    if salary_min is not None and salary_max is not None and salary_max < salary_min:
        raise ValueError({'salary_max': 'Maximum salary must be >= minimum salary.'})

    user = User(
        username=generate_username(account_email),
        email=account_email,
        phone_number=whatsapp_number,
        user_role=User.Role.EMPLOYER,
        first_name=employer_data.get('contact_person', '')[:30],
    )
    user.set_password(secrets.token_urlsafe(24))
    user.save()

    employer = user.employer_profile
    employer.organization_type = employer_data['organization_type']
    employer.organization_name = employer_data['organization_name']
    employer.description = employer_data.get('description', '')
    employer.contact_person = employer_data['contact_person']
    employer.province = employer_province
    employer.city = employer_city
    employer.district = employer_district
    employer.whatsapp_number = whatsapp_number
    employer.contact_phone = contact_phone
    employer.contact_email = contact_email or None
    employer.created_by_admin = True
    employer.admin_notes = admin_notes
    employer.save()

    required_languages = list(job_data.get('required_languages') or [])
    job_fields = {
        key: value for key, value in job_data.items() if key != 'required_languages'
    }
    job = JobPosting.objects.create(
        employer=employer,
        status=JobPosting.Status.ACTIVE,
        **job_fields,
    )
    if required_languages:
        job.required_languages.set(required_languages)

    return employer, job
