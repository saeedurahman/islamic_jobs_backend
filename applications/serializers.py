from django.utils import timezone
from rest_framework import serializers

from jobs.models import JobPosting
from profiles.serializers import ApplicantProfileWithContactSerializer

from .models import Application

APPLICANT_PROFILE_SELECT_RELATED = (
    'applicant',
    'applicant__user',
    'applicant__province',
    'applicant__city',
    'applicant__district',
    'applicant__village',
)

APPLICANT_PROFILE_PREFETCH = (
    'applicant__hifz_records',
    'applicant__dars_nizami_records',
    'applicant__mufti_course_records',
    'applicant__ijazah_records',
    'applicant__nazra_qirat_records',
    'applicant__asri_education_records',
    'applicant__languages',
    'applicant__skills',
)


class JobApplicationSummarySerializer(serializers.ModelSerializer):
    employer_organization_name = serializers.CharField(
        source='employer.organization_name',
        read_only=True,
    )
    city_name = serializers.SerializerMethodField()

    class Meta:
        model = JobPosting
        fields = ['id', 'title', 'employer_organization_name', 'city_name', 'status']

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['job', 'cover_note']

    def validate_job(self, job):
        if job.status != JobPosting.Status.ACTIVE:
            raise serializers.ValidationError(
                'This job posting is no longer accepting applications.'
            )
        if job.expires_at and job.expires_at <= timezone.now():
            raise serializers.ValidationError('This job posting has expired.')
        return job

    def validate(self, attrs):
        request = self.context['request']
        try:
            profile = request.user.profile
        except Exception:
            raise serializers.ValidationError('Job seeker profile not found.')

        job = attrs['job']
        existing = Application.objects.filter(job=job, applicant=profile).first()
        if existing and existing.status in Application.ACTIVE_STATUSES:
            raise serializers.ValidationError(
                {'job': 'You have already applied to this job.'}
            )
        attrs['applicant'] = profile
        attrs['existing_application'] = existing
        return attrs

    def create(self, validated_data):
        existing = validated_data.pop('existing_application', None)
        applicant = validated_data.pop('applicant')
        cover_note = validated_data.get('cover_note', '')

        if existing:
            existing.status = Application.Status.APPLIED
            existing.cover_note = cover_note
            existing.save(update_fields=['status', 'cover_note', 'status_updated_at'])
            return existing

        return Application.objects.create(applicant=applicant, **validated_data)


class ApplicationSeekerSerializer(serializers.ModelSerializer):
    job = JobApplicationSummarySerializer(read_only=True)

    class Meta:
        model = Application
        fields = [
            'id',
            'job',
            'status',
            'cover_note',
            'applied_at',
            'status_updated_at',
        ]


class ApplicationEmployerSerializer(serializers.ModelSerializer):
    applicant = ApplicantProfileWithContactSerializer(read_only=True)

    class Meta:
        model = Application
        fields = [
            'id',
            'applicant',
            'status',
            'cover_note',
            'applied_at',
            'status_updated_at',
        ]


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status']

    def validate_status(self, value):
        allowed = {
            Application.Status.APPLIED,
            Application.Status.SHORTLISTED,
            Application.Status.INTERVIEW,
            Application.Status.HIRED,
            Application.Status.REJECTED,
        }
        if value not in allowed:
            raise serializers.ValidationError('Invalid status for employer update.')
        return value
