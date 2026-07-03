from django.conf import settings
from django.db import models

from profiles.validators import (
    validate_verification_document_extension,
    validate_verification_document_size,
)


class Employer(models.Model):
    class OrganizationType(models.TextChoices):
        MASJID = 'masjid', 'Masjid'
        MADRASA = 'madrasa', 'Madrasa'
        NGO = 'ngo', 'NGO'
        SCHOOL = 'school', 'School'
        UNIVERSITY = 'university', 'University'
        INDIVIDUAL = 'individual', 'Individual'

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employer_profile',
    )
    organization_type = models.CharField(
        max_length=20,
        choices=OrganizationType.choices,
        null=True,
        blank=True,
    )
    organization_name = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField(blank=True)
    contact_person = models.CharField(max_length=200, blank=True, default='')

    province = models.ForeignKey(
        'locations.Province',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employers',
    )
    city = models.ForeignKey(
        'locations.City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employers',
    )
    district = models.ForeignKey(
        'locations.District',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employers',
    )
    village = models.ForeignKey(
        'locations.Village',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employers',
    )

    whatsapp_number = models.CharField(max_length=15, blank=True, default='')
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)

    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verification_document = models.FileField(
        upload_to='employers/verification_docs/',
        null=True,
        blank=True,
        validators=[
            validate_verification_document_extension,
            validate_verification_document_size,
        ],
    )

    created_by_admin = models.BooleanField(
        default=False,
        help_text='Created on behalf of the organization by a platform admin.',
    )
    admin_notes = models.TextField(
        blank=True,
        help_text='Internal admin-only notes (never shown publicly).',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.organization_name or f'Employer of {self.user.email}'

    def is_visible_publicly(self):
        return self.verification_status == self.VerificationStatus.VERIFIED
