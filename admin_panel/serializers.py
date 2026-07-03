from rest_framework import serializers

from accounts.models import User
from accounts.utils import is_valid_pakistani_phone, normalize_phone_number
from employers.models import Employer
from jobs.models import JobPosting
from jobs.serializers import JobOwnerSerializer
from locations.models import City, District, Province
from profiles.models import Language, Profile
from profiles.serializers import ProfilePublicSerializer
from profiles.validators import get_location_consistency_errors

from .services import create_admin_employer_and_job


class AdminProfileDetailSerializer(ProfilePublicSerializer):
    """Full profile for admin review, including verification document."""

    email = serializers.EmailField(source='user.email', read_only=True)
    contact_phone = serializers.CharField(read_only=True)
    contact_email = serializers.EmailField(read_only=True)
    passport_number = serializers.CharField(read_only=True)
    verification_document = serializers.FileField(read_only=True)
    is_public = serializers.BooleanField(read_only=True)
    profile_completion_percentage = serializers.IntegerField(read_only=True)

    class Meta(ProfilePublicSerializer.Meta):
        fields = ProfilePublicSerializer.Meta.fields + [
            'email',
            'contact_phone',
            'contact_email',
            'passport_number',
            'verification_document',
            'is_public',
            'is_disabled',
            'profile_completion_percentage',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and data.get('verification_document'):
            data['verification_document'] = request.build_absolute_uri(
                data['verification_document']
            )
        return data


class AdminEmployerDetailSerializer(serializers.ModelSerializer):
    """Full employer record for admin review, including verification document."""

    province_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    district_name = serializers.SerializerMethodField()
    village_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Employer
        fields = [
            'id',
            'organization_type',
            'organization_name',
            'description',
            'contact_person',
            'province_name',
            'city_name',
            'district_name',
            'village_name',
            'whatsapp_number',
            'contact_phone',
            'contact_email',
            'verification_status',
            'verification_document',
            'created_by_admin',
            'admin_notes',
            'email',
            'created_at',
            'updated_at',
        ]

    def get_province_name(self, obj):
        return obj.province.name if obj.province else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None

    def get_district_name(self, obj):
        return obj.district.name if obj.district else None

    def get_village_name(self, obj):
        return obj.village.name if obj.village else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and data.get('verification_document'):
            data['verification_document'] = request.build_absolute_uri(
                data['verification_document']
            )
        return data


class AdminProfileListSerializer(serializers.ModelSerializer):
    province_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'full_name',
            'user_category',
            'city_name',
            'province_name',
            'verification_status',
            'is_public',
            'is_disabled',
            'profile_completion_percentage',
            'email',
            'created_at',
        ]

    def get_province_name(self, obj):
        return obj.province.name if obj.province else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None


class AdminEmployerListSerializer(serializers.ModelSerializer):
    province_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Employer
        fields = [
            'id',
            'organization_name',
            'organization_type',
            'contact_person',
            'city_name',
            'province_name',
            'verification_status',
            'email',
            'created_at',
        ]

    def get_province_name(self, obj):
        return obj.province.name if obj.province else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None


class AdminJobListSerializer(serializers.ModelSerializer):
    employer_organization_name = serializers.CharField(
        source='employer.organization_name',
        read_only=True,
    )

    class Meta:
        model = JobPosting
        fields = [
            'id',
            'title',
            'employer_organization_name',
            'category',
            'status',
            'created_at',
        ]


class AdminUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'user_role',
            'created_at',
        ]


class VerificationStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['verified', 'rejected'])

    def validate_status(self, value):
        return value


class AdminEmployerCreateInputSerializer(serializers.Serializer):
    organization_type = serializers.ChoiceField(choices=Employer.OrganizationType.choices)
    organization_name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    contact_person = serializers.CharField(max_length=200)
    province = serializers.PrimaryKeyRelatedField(queryset=Province.objects.all())
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    district = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        required=False,
        allow_null=True,
    )
    whatsapp_number = serializers.CharField(max_length=15)
    contact_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    def validate_whatsapp_number(self, value):
        normalized = normalize_phone_number(value)
        if not is_valid_pakistani_phone(normalized):
            raise serializers.ValidationError(
                'Enter a valid Pakistani phone number (e.g. 03001234567 or +923001234567).'
            )
        return normalized

    def validate_contact_phone(self, value):
        if value in (None, ''):
            return value
        normalized = normalize_phone_number(value)
        if not is_valid_pakistani_phone(normalized):
            raise serializers.ValidationError(
                'Enter a valid Pakistani phone number (e.g. 03001234567 or +923001234567).'
            )
        return normalized

    def validate(self, attrs):
        errors = get_location_consistency_errors(
            attrs['province'],
            attrs['city'],
            district=attrs.get('district'),
        )
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class AdminJobCreateInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    category = serializers.ChoiceField(choices=Profile.UserCategory.choices)
    province = serializers.PrimaryKeyRelatedField(queryset=Province.objects.all())
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    district = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        required=False,
        allow_null=True,
    )
    salary_min = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    salary_max = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    accommodation_provided = serializers.BooleanField(default=False)
    meals_provided = serializers.BooleanField(default=False)
    experience_required = serializers.ChoiceField(choices=JobPosting.ExperienceRequired.choices)
    sect = serializers.ChoiceField(
        choices=JobPosting.Sect.choices,
        required=False,
        allow_null=True,
    )
    required_languages = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Language.objects.all(),
        required=False,
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')
        if salary_min is not None and salary_max is not None and salary_max < salary_min:
            raise serializers.ValidationError(
                {'salary_max': 'Maximum salary must be greater than or equal to minimum salary.'}
            )

        errors = get_location_consistency_errors(
            attrs['province'],
            attrs['city'],
            district=attrs.get('district'),
        )
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class AdminCreateEmployerAndJobSerializer(serializers.Serializer):
    admin_notes = serializers.CharField(required=False, allow_blank=True, default='')
    employer = AdminEmployerCreateInputSerializer()
    job = AdminJobCreateInputSerializer()

    def create(self, validated_data):
        employer_data = validated_data['employer']
        job_data = validated_data['job']
        admin_notes = validated_data.get('admin_notes', '')

        try:
            employer, job = create_admin_employer_and_job(
                employer_data=employer_data,
                job_data=job_data,
                admin_notes=admin_notes,
            )
        except ValueError as exc:
            detail = exc.args[0]
            if isinstance(detail, dict):
                raise serializers.ValidationError(detail) from exc
            raise serializers.ValidationError({'detail': str(detail)}) from exc

        return {'employer': employer, 'job': job}


class AdminCreateEmployerAndJobResponseSerializer(serializers.Serializer):
    employer = AdminEmployerDetailSerializer()
    job = JobOwnerSerializer()
    message = serializers.CharField()
    account_email = serializers.EmailField()

    def to_representation(self, instance):
        employer = instance['employer']
        job = (
            JobPosting.objects.select_related(
                'employer', 'employer__city', 'province', 'city', 'district'
            )
            .prefetch_related('required_languages')
            .get(pk=instance['job'].pk)
        )
        return {
            'employer': AdminEmployerDetailSerializer(
                employer,
                context=self.context,
            ).data,
            'job': JobOwnerSerializer(job, context=self.context).data,
            'account_email': employer.user.email,
            'message': (
                'Employer account and job created successfully. '
                'The employer remains pending document verification. '
                'Login credentials were not included in this response; '
                'reset the password via Django admin if the organization needs access later.'
            ),
        }
