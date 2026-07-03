from rest_framework import serializers

from .models import City, District, Province, Village


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'name', 'name_urdu', 'slug']


class ProvinceSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'name', 'slug']


class CitySerializer(serializers.ModelSerializer):
    province_id = serializers.PrimaryKeyRelatedField(
        source='province',
        read_only=True,
    )
    province = ProvinceSummarySerializer(read_only=True)

    class Meta:
        model = City
        fields = ['id', 'name', 'name_urdu', 'slug', 'province_id', 'province']


class DistrictSerializer(serializers.ModelSerializer):
    city_id = serializers.PrimaryKeyRelatedField(
        source='city',
        read_only=True,
    )

    class Meta:
        model = District
        fields = ['id', 'name', 'name_urdu', 'city_id']


class VillageSerializer(serializers.ModelSerializer):
    district_id = serializers.PrimaryKeyRelatedField(
        source='district',
        read_only=True,
    )

    class Meta:
        model = Village
        fields = ['id', 'name', 'district_id']
