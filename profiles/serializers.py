from rest_framework import serializers

from accounts.utils import is_valid_pakistani_phone, normalize_phone_number

from .models import (
    AsriEducation,
    DarseNizami,
    HifzEducation,
    Ijazah,
    Language,
    MuftiCourse,
    NazraQirat,
    Profile,
    Skill,
)


class AgeMixin(serializers.Serializer):
    age = serializers.SerializerMethodField()

    def get_age(self, obj):
        return obj.age


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'name_urdu']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'name_urdu']


class HifzEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HifzEducation
        fields = ['id', 'madrasa_name', 'completion_year', 'teacher_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class DarseNizamiSerializer(serializers.ModelSerializer):
    class Meta:
        model = DarseNizami
        fields = ['id', 'madrasa_name', 'wifaq_name', 'sanad_year', 'created_at']
        read_only_fields = ['id', 'created_at']


class MuftiCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuftiCourse
        fields = ['id', 'madrasa_name', 'takhassus_subject', 'completion_year', 'created_at']
        read_only_fields = ['id', 'created_at']


class IjazahSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ijazah
        fields = ['id', 'subject', 'ustad_name', 'year', 'created_at']
        read_only_fields = ['id', 'created_at']


class NazraQiratSerializer(serializers.ModelSerializer):
    class Meta:
        model = NazraQirat
        fields = [
            'id',
            'type',
            'qirat_type',
            'madrasa_or_teacher',
            'completion_year',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AsriEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsriEducation
        fields = ['id', 'level', 'institution', 'year', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProfileOwnerSerializer(AgeMixin, serializers.ModelSerializer):
    hifz_records = HifzEducationSerializer(many=True, read_only=True)
    dars_nizami_records = DarseNizamiSerializer(many=True, read_only=True)
    mufti_course_records = MuftiCourseSerializer(many=True, read_only=True)
    ijazah_records = IjazahSerializer(many=True, read_only=True)
    nazra_qirat_records = NazraQiratSerializer(many=True, read_only=True)
    asri_education_records = AsriEducationSerializer(many=True, read_only=True)
    languages = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Language.objects.all(),
        required=False,
    )
    skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all(),
        required=False,
    )
    languages_detail = LanguageSerializer(source='languages', many=True, read_only=True)
    skills_detail = SkillSerializer(source='skills', many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'full_name',
            'father_name',
            'date_of_birth',
            'age',
            'marital_status',
            'passport_number',
            'whatsapp_number',
            'contact_phone',
            'contact_email',
            'province',
            'city',
            'district',
            'village',
            'user_category',
            'languages',
            'languages_detail',
            'skills',
            'skills_detail',
            'audio_sample',
            'video_sample',
            'verification_document',
            'verification_status',
            'is_public',
            'show_contact_publicly',
            'profile_completion_percentage',
            'hifz_records',
            'dars_nizami_records',
            'mufti_course_records',
            'ijazah_records',
            'nazra_qirat_records',
            'asri_education_records',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'verification_status',
            'profile_completion_percentage',
            'languages_detail',
            'skills_detail',
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

        if city and province and city.province_id != province.id:
            raise serializers.ValidationError(
                {'city': 'Selected city does not belong to the selected province.'}
            )
        if district and city and district.city_id != city.id:
            raise serializers.ValidationError(
                {'district': 'Selected district does not belong to the selected city.'}
            )
        if village and district and village.district_id != district.id:
            raise serializers.ValidationError(
                {'village': 'Selected village does not belong to the selected district.'}
            )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            for field_name in ('audio_sample', 'video_sample', 'verification_document'):
                if data.get(field_name):
                    data[field_name] = request.build_absolute_uri(data[field_name])
        return data


def shows_contact_publicly(profile):
    return (
        profile.show_contact_publicly
        and profile.verification_status == Profile.VerificationStatus.VERIFIED
    )


class ProfilePublicSerializer(AgeMixin, serializers.ModelSerializer):
    province_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    district_name = serializers.SerializerMethodField()
    village_name = serializers.SerializerMethodField()
    contact_email = serializers.SerializerMethodField()
    whatsapp_number = serializers.SerializerMethodField()
    hifz_records = HifzEducationSerializer(many=True, read_only=True)
    dars_nizami_records = DarseNizamiSerializer(many=True, read_only=True)
    mufti_course_records = MuftiCourseSerializer(many=True, read_only=True)
    ijazah_records = IjazahSerializer(many=True, read_only=True)
    nazra_qirat_records = NazraQiratSerializer(many=True, read_only=True)
    asri_education_records = AsriEducationSerializer(many=True, read_only=True)
    languages_detail = LanguageSerializer(source='languages', many=True, read_only=True)
    skills_detail = SkillSerializer(source='skills', many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'full_name',
            'father_name',
            'date_of_birth',
            'age',
            'marital_status',
            'province_name',
            'city_name',
            'district_name',
            'village_name',
            'user_category',
            'verification_status',
            'is_public',
            'contact_email',
            'whatsapp_number',
            'languages_detail',
            'skills_detail',
            'audio_sample',
            'video_sample',
            'hifz_records',
            'dars_nizami_records',
            'mufti_course_records',
            'ijazah_records',
            'nazra_qirat_records',
            'asri_education_records',
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

    def get_contact_email(self, obj):
        if shows_contact_publicly(obj):
            return obj.contact_email
        return None

    def get_whatsapp_number(self, obj):
        if shows_contact_publicly(obj):
            return obj.whatsapp_number or None
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            for field_name in ('audio_sample', 'video_sample'):
                if data.get(field_name):
                    data[field_name] = request.build_absolute_uri(data[field_name])
        return data


class ApplicantProfileWithContactSerializer(ProfilePublicSerializer):
    """Public profile fields plus contact info for employers reviewing their applicants."""

    contact_email = serializers.SerializerMethodField()
    whatsapp_number = serializers.CharField(read_only=True)

    def get_contact_email(self, obj):
        return obj.contact_email or obj.user.email


class ProfileListSerializer(serializers.ModelSerializer):
    province_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    has_hifz = serializers.SerializerMethodField()
    has_dars_nizami = serializers.SerializerMethodField()

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
            'has_hifz',
            'has_dars_nizami',
            'updated_at',
        ]

    def get_province_name(self, obj):
        return obj.province.name if obj.province else None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None

    def get_has_hifz(self, obj):
        prefetched = getattr(obj, '_prefetched_objects_cache', {})
        if 'hifz_records' in prefetched:
            return bool(prefetched['hifz_records'])
        return obj.hifz_records.exists()

    def get_has_dars_nizami(self, obj):
        prefetched = getattr(obj, '_prefetched_objects_cache', {})
        if 'dars_nizami_records' in prefetched:
            return bool(prefetched['dars_nizami_records'])
        return obj.dars_nizami_records.exists()
