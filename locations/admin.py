from django.contrib import admin

from .models import City, District, Province, Village


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_urdu', 'slug']
    search_fields = ['name', 'name_urdu', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_urdu', 'slug', 'province']
    list_filter = ['province']
    search_fields = ['name', 'name_urdu', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_urdu', 'city', 'province_name']
    list_filter = ['city__province', 'city']
    search_fields = ['name', 'name_urdu']

    @admin.display(description='Province')
    def province_name(self, obj):
        return obj.city.province.name


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'city_name', 'province_name']
    list_filter = ['district__city__province', 'district__city']
    search_fields = ['name']

    @admin.display(description='City')
    def city_name(self, obj):
        return obj.district.city.name

    @admin.display(description='Province')
    def province_name(self, obj):
        return obj.district.city.province.name
