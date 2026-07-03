from datetime import date

from django.core.exceptions import ValidationError

MB = 1024 * 1024
AUDIO_MAX_SIZE = 20 * MB
VIDEO_MAX_SIZE = 100 * MB
VERIFICATION_DOC_MAX_SIZE = 10 * MB


def validate_education_year(value):
    if value is None:
        return
    current_year = date.today().year
    if value < 1950 or value > current_year:
        raise ValidationError(
            f'Year must be between 1950 and {current_year}.',
            code='invalid_year',
        )


def validate_audio_file_size(value):
    if value and value.size > AUDIO_MAX_SIZE:
        raise ValidationError(
            f'Audio file size must not exceed {AUDIO_MAX_SIZE // MB} MB.',
            code='audio_too_large',
        )


def validate_video_file_size(value):
    if value and value.size > VIDEO_MAX_SIZE:
        raise ValidationError(
            f'Video file size must not exceed {VIDEO_MAX_SIZE // MB} MB.',
            code='video_too_large',
        )


def validate_verification_document_size(value):
    if value and value.size > VERIFICATION_DOC_MAX_SIZE:
        raise ValidationError(
            f'Verification document size must not exceed {VERIFICATION_DOC_MAX_SIZE // MB} MB.',
            code='verification_doc_too_large',
        )


VERIFICATION_DOC_EXTENSIONS = ('pdf', 'jpg', 'jpeg', 'png', 'webp')


def validate_verification_document_extension(value):
    if not value:
        return
    extension = value.name.rsplit('.', 1)[-1].lower()
    if extension not in VERIFICATION_DOC_EXTENSIONS:
        raise ValidationError(
            'Verification document must be a PDF or image file (pdf, jpg, jpeg, png, webp).',
            code='invalid_verification_doc_extension',
        )


def get_location_consistency_errors(province, city, district=None, village=None):
    """Return field-level errors for mismatched location hierarchy, or an empty dict."""
    errors = {}
    if city and province and city.province_id != province.id:
        errors['city'] = 'Selected city does not belong to the selected province.'
    if district and city and district.city_id != city.id:
        errors['district'] = 'Selected district does not belong to the selected city.'
    if village and district and village.district_id != district.id:
        errors['village'] = 'Selected village does not belong to the selected district.'
    return errors
