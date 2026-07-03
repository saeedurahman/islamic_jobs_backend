from rest_framework import serializers

from accounts.utils import is_valid_pakistani_phone, normalize_phone_number
from profiles.validators import get_location_consistency_errors

from .models import Employer


class EmployerOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = [
            'id',
            'organization_type',
            'organization_name',
            'description',
            'contact_person',
            'province',
            'city',
            'district',
            'village',
            'whatsapp_number',
            'contact_phone',
            'contact_email',
            'verification_status',
            'verification_document',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'verification_status',
            'created_at',
            'updated_at',
        ]

    def _normalize_optional_phone(self, value):
        if value in (None, ''):
            return value
        normalized = normalize_phone_number(value)
        if not is_valid_pakistani_phone(normalized):
            raise serializers.ValidationError(
                'Enter a valid Pakistani phone number (e.g. 03001234567 or +923001234567).'
            )
        return normalized

    def validate_whatsapp_number(self, value):
        if not value:
            return value
        return self._normalize_optional_phone(value)

    def validate_contact_phone(self, value):
        return self._normalize_optional_phone(value)

    def validate(self, attrs):
        province = attrs.get('province', getattr(self.instance, 'province', None) if self.instance else None)
        city = attrs.get('city', getattr(self.instance, 'city', None) if self.instance else None)
        district = attrs.get('district', getattr(self.instance, 'district', None) if self.instance else None)
        village = attrs.get('village', getattr(self.instance, 'village', None) if self.instance else None)

        errors = get_location_consistency_errors(province, city, district, village)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and data.get('verification_document'):
            data['verification_document'] = request.build_absolute_uri(
                data['verification_document']
            )
        return data


class EmployerPublicSerializer(serializers.ModelSerializer):
    province_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    district_name = serializers.SerializerMethodField()
    village_name = serializers.SerializerMethodField()

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
