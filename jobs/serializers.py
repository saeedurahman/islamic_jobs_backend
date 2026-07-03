from rest_framework import serializers

from employers.models import Employer
from profiles.models import Language
from profiles.serializers import LanguageSerializer
from profiles.validators import get_location_consistency_errors

from .models import JobPosting


class EmployerJobSummarySerializer(serializers.ModelSerializer):
    city_name = serializers.SerializerMethodField()

    class Meta:
        model = Employer
        fields = ['id', 'organization_name', 'organization_type', 'city_name']

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None


class JobPublicEmployerSummarySerializer(serializers.ModelSerializer):
    city_name = serializers.SerializerMethodField()
    whatsapp_number = serializers.SerializerMethodField()

    class Meta:
        model = Employer
        fields = [
            'id',
            'organization_name',
            'organization_type',
            'city_name',
            'whatsapp_number',
        ]

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None

    def get_whatsapp_number(self, obj):
        if (
            obj.verification_status == Employer.VerificationStatus.VERIFIED
            or obj.created_by_admin
        ):
            return obj.whatsapp_number or None
        return None


class JobOwnerSerializer(serializers.ModelSerializer):
    employer = EmployerJobSummarySerializer(read_only=True)
    required_languages = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Language.objects.all(),
        required=False,
    )
    required_languages_detail = LanguageSerializer(
        source='required_languages',
        many=True,
        read_only=True,
    )

    class Meta:
        model = JobPosting
        fields = [
            'id',
            'employer',
            'title',
            'description',
            'category',
            'province',
            'city',
            'district',
            'salary_min',
            'salary_max',
            'accommodation_provided',
            'meals_provided',
            'experience_required',
            'sect',
            'required_languages',
            'required_languages_detail',
            'status',
            'created_at',
            'updated_at',
            'expires_at',
        ]
        read_only_fields = ['id', 'employer', 'created_at', 'updated_at', 'required_languages_detail']

    def validate(self, attrs):
        salary_min = attrs.get('salary_min', getattr(self.instance, 'salary_min', None) if self.instance else None)
        salary_max = attrs.get('salary_max', getattr(self.instance, 'salary_max', None) if self.instance else None)
        if salary_min is not None and salary_max is not None and salary_max < salary_min:
            raise serializers.ValidationError(
                {'salary_max': 'Maximum salary must be greater than or equal to minimum salary.'}
            )

        province = attrs.get('province', getattr(self.instance, 'province', None) if self.instance else None)
        city = attrs.get('city', getattr(self.instance, 'city', None) if self.instance else None)
        district = attrs.get('district', getattr(self.instance, 'district', None) if self.instance else None)

        errors = get_location_consistency_errors(province, city, district=district)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class JobPublicSerializer(serializers.ModelSerializer):
    province_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    district_name = serializers.SerializerMethodField()
    employer = JobPublicEmployerSummarySerializer(read_only=True)
    required_languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = JobPosting
        fields = [
            'id',
            'title',
            'description',
            'category',
            'province_name',
            'city_name',
            'district_name',
            'salary_min',
            'salary_max',
            'accommodation_provided',
            'meals_provided',
            'experience_required',
            'sect',
            'required_languages',
            'employer',
            'status',
            'created_at',
            'updated_at',
            'expires_at',
        ]

    def get_province_name(self, obj):
        return obj.province.name if obj.province else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None

    def get_district_name(self, obj):
        return obj.district.name if obj.district else None


class JobListSerializer(serializers.ModelSerializer):
    province_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()

    class Meta:
        model = JobPosting
        fields = [
            'id',
            'title',
            'category',
            'city_name',
            'province_name',
            'salary_min',
            'salary_max',
            'experience_required',
            'status',
            'created_at',
        ]

    def get_province_name(self, obj):
        return obj.province.name if obj.province else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None
