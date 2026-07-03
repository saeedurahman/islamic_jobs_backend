from datetime import date

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from profiles.validators import (
    validate_audio_file_size,
    validate_education_year,
    validate_verification_document_size,
    validate_video_file_size,
)


class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    name_urdu = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    name_urdu = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Profile(models.Model):
    class MaritalStatus(models.TextChoices):
        SINGLE = 'single', 'Single'
        MARRIED = 'married', 'Married'
        DIVORCED = 'divorced', 'Divorced'
        WIDOWED = 'widowed', 'Widowed'

    class UserCategory(models.TextChoices):
        IMAM = 'imam', 'Imam'
        MUAZZIN = 'muazzin', 'Muazzin'
        MUDARRIS = 'mudarris', 'Mudarris'
        MUFTI = 'mufti', 'Mufti'
        QARI = 'qari', 'Qari'
        KHATEEB = 'khateeb', 'Khateeb'
        QURAN_TEACHER = 'quran_teacher', 'Quran Teacher'
        ISLAMIC_LECTURER = 'islamic_lecturer', 'Islamic Lecturer'
        INDIVIDUAL = 'individual', 'Individual'

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    full_name = models.CharField(max_length=200, blank=True, default='')
    father_name = models.CharField(max_length=200, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    marital_status = models.CharField(
        max_length=20,
        choices=MaritalStatus.choices,
        null=True,
        blank=True,
    )
    passport_number = models.CharField(max_length=50, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=15, blank=True, default='')
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)

    province = models.ForeignKey(
        'locations.Province',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
    )
    city = models.ForeignKey(
        'locations.City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
    )
    district = models.ForeignKey(
        'locations.District',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
    )
    village = models.ForeignKey(
        'locations.Village',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
    )

    user_category = models.CharField(
        max_length=30,
        choices=UserCategory.choices,
        null=True,
        blank=True,
    )
    languages = models.ManyToManyField(Language, blank=True, related_name='profiles')
    skills = models.ManyToManyField(Skill, blank=True, related_name='profiles')

    audio_sample = models.FileField(
        upload_to='profiles/audio/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(['mp3', 'wav', 'm4a']),
            validate_audio_file_size,
        ],
    )
    video_sample = models.FileField(
        upload_to='profiles/video/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(['mp4', 'mov', 'avi']),
            validate_video_file_size,
        ],
    )
    verification_document = models.FileField(
        upload_to='profiles/verification_docs/',
        null=True,
        blank=True,
        validators=[validate_verification_document_size],
    )

    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    is_public = models.BooleanField(default=False)
    show_contact_publicly = models.BooleanField(
        default=False,
        help_text='When verified, allow contact email and WhatsApp on the public profile.',
    )
    profile_completion_percentage = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name or f'Profile of {self.user.email}'

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return years

    def is_visible_publicly(self):
        return (
            self.is_public
            and self.verification_status == self.VerificationStatus.VERIFIED
        )

    def _has_personal_info_complete(self):
        return all([
            self.full_name,
            self.father_name,
            self.date_of_birth,
            self.marital_status,
            self.whatsapp_number,
            self.province_id,
            self.city_id,
        ])

    def _has_islamic_education(self):
        return any([
            self.hifz_records.exists(),
            self.dars_nizami_records.exists(),
            self.mufti_course_records.exists(),
            self.ijazah_records.exists(),
            self.nazra_qirat_records.exists(),
        ])

    def calculate_completion_percentage(self):
        score = 0

        if self._has_personal_info_complete():
            score += 30

        if self._has_islamic_education():
            score += 25

        if self.asri_education_records.exists():
            score += 10

        if self.languages.exists():
            score += 10

        if self.skills.exists():
            score += 10

        if self.audio_sample or self.video_sample:
            score += 10

        if self.verification_document:
            score += 5

        return min(score, 100)


class HifzEducation(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='hifz_records',
    )
    madrasa_name = models.CharField(max_length=200)
    completion_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_education_year],
    )
    teacher_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [models.F('completion_year').desc(nulls_last=True), '-created_at']
        verbose_name = 'Hifz education'
        verbose_name_plural = 'Hifz education records'

    def __str__(self):
        return f'{self.madrasa_name} — {self.profile}'


class DarseNizami(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='dars_nizami_records',
    )
    madrasa_name = models.CharField(max_length=200)
    wifaq_name = models.CharField(max_length=200, blank=True)
    sanad_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_education_year],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [models.F('sanad_year').desc(nulls_last=True), '-created_at']
        verbose_name = 'Dars-e-Nizami'
        verbose_name_plural = 'Dars-e-Nizami records'

    def __str__(self):
        return f'{self.madrasa_name} — {self.profile}'


class MuftiCourse(models.Model):
    class TakhassusSubject(models.TextChoices):
        HADITH = 'hadith', 'Hadith'
        FIQH = 'fiqh', 'Fiqh'
        TAFSIR = 'tafsir', 'Tafsir'
        ARABIC = 'arabic', 'Arabic'
        OTHER = 'other', 'Other'

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='mufti_course_records',
    )
    madrasa_name = models.CharField(max_length=200)
    takhassus_subject = models.CharField(max_length=20, choices=TakhassusSubject.choices)
    completion_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_education_year],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [models.F('completion_year').desc(nulls_last=True), '-created_at']
        verbose_name = 'Mufti course'
        verbose_name_plural = 'Mufti course records'

    def __str__(self):
        return f'{self.madrasa_name} ({self.takhassus_subject}) — {self.profile}'


class Ijazah(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='ijazah_records',
    )
    subject = models.CharField(max_length=200)
    ustad_name = models.CharField(max_length=200)
    year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_education_year],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [models.F('year').desc(nulls_last=True), '-created_at']
        verbose_name_plural = 'Ijazah records'

    def __str__(self):
        return f'{self.subject} — {self.profile}'


class NazraQirat(models.Model):
    class Type(models.TextChoices):
        NAZRA = 'nazra', 'Nazra'
        TAJWEED = 'tajweed', 'Tajweed'
        QIRAT = 'qirat', 'Qirat'

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='nazra_qirat_records',
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    qirat_type = models.CharField(max_length=200, blank=True, null=True)
    madrasa_or_teacher = models.CharField(max_length=200, blank=True)
    completion_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_education_year],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [models.F('completion_year').desc(nulls_last=True), '-created_at']
        verbose_name = 'Nazra/Qirat'
        verbose_name_plural = 'Nazra/Qirat records'

    def __str__(self):
        return f'{self.get_type_display()} — {self.profile}'


class AsriEducation(models.Model):
    class Level(models.TextChoices):
        MATRIC = 'matric', 'Matric'
        FA = 'fa', 'FA'
        BA = 'ba', 'BA'
        MA = 'ma', 'MA'
        BS = 'bs', 'BS'
        MPHIL = 'mphil', 'MPhil'
        PHD = 'phd', 'PhD'

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='asri_education_records',
    )
    level = models.CharField(max_length=20, choices=Level.choices)
    institution = models.CharField(max_length=200)
    year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_education_year],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [models.F('year').desc(nulls_last=True), '-created_at']
        verbose_name = 'Asri education'
        verbose_name_plural = 'Asri education records'

    def __str__(self):
        return f'{self.get_level_display()} — {self.institution}'
