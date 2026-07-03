from django.contrib import admin
from django.utils.html import format_html

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


@admin.action(description='Mark selected profiles as verified')
def mark_as_verified(modeladmin, request, queryset):
    updated = queryset.update(verification_status=Profile.VerificationStatus.VERIFIED)
    modeladmin.message_user(request, f'{updated} profile(s) marked as verified.')


class HifzEducationInline(admin.TabularInline):
    model = HifzEducation
    extra = 0
    fields = ['madrasa_name', 'completion_year', 'teacher_name', 'created_at']
    readonly_fields = ['created_at']


class DarseNizamiInline(admin.TabularInline):
    model = DarseNizami
    extra = 0
    fields = ['madrasa_name', 'wifaq_name', 'sanad_year', 'created_at']
    readonly_fields = ['created_at']


class MuftiCourseInline(admin.TabularInline):
    model = MuftiCourse
    extra = 0
    fields = ['madrasa_name', 'takhassus_subject', 'completion_year', 'created_at']
    readonly_fields = ['created_at']


class IjazahInline(admin.TabularInline):
    model = Ijazah
    extra = 0
    fields = ['subject', 'ustad_name', 'year', 'created_at']
    readonly_fields = ['created_at']


class NazraQiratInline(admin.TabularInline):
    model = NazraQirat
    extra = 0
    fields = ['type', 'qirat_type', 'madrasa_or_teacher', 'completion_year', 'created_at']
    readonly_fields = ['created_at']


class AsriEducationInline(admin.TabularInline):
    model = AsriEducation
    extra = 0
    fields = ['level', 'institution', 'year', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'full_name',
        'user_category',
        'city',
        'verification_status',
        'is_public',
        'profile_completion_percentage',
        'created_at',
    ]
    list_filter = ['verification_status', 'user_category', 'is_public', 'province']
    search_fields = ['full_name', 'father_name']
    raw_id_fields = ['user', 'province', 'city', 'district', 'village']
    filter_horizontal = ['languages', 'skills']
    readonly_fields = [
        'created_at',
        'updated_at',
        'profile_completion_percentage',
        'audio_sample_link',
        'video_sample_link',
        'verification_document_link',
    ]
    actions = [mark_as_verified]
    inlines = [
        HifzEducationInline,
        DarseNizamiInline,
        MuftiCourseInline,
        IjazahInline,
        NazraQiratInline,
        AsriEducationInline,
    ]

    fieldsets = (
        (None, {
            'fields': (
                'user',
                'full_name',
                'father_name',
                'date_of_birth',
                'marital_status',
                'user_category',
            ),
        }),
        ('Contact', {
            'fields': (
                'whatsapp_number',
                'contact_phone',
                'contact_email',
                'passport_number',
            ),
        }),
        ('Location', {
            'fields': ('province', 'city', 'district', 'village'),
        }),
        ('Languages & Skills', {
            'fields': ('languages', 'skills'),
        }),
        ('Media & Verification', {
            'fields': (
                'audio_sample',
                'audio_sample_link',
                'video_sample',
                'video_sample_link',
                'verification_document',
                'verification_document_link',
                'verification_status',
                'is_public',
                'profile_completion_percentage',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Audio sample')
    def audio_sample_link(self, obj):
        if obj.audio_sample:
            return format_html(
                '<a href="{}" target="_blank">Listen to audio sample</a>',
                obj.audio_sample.url,
            )
        return '—'

    @admin.display(description='Video sample')
    def video_sample_link(self, obj):
        if obj.video_sample:
            return format_html(
                '<a href="{}" target="_blank">Watch video sample</a>',
                obj.video_sample.url,
            )
        return '—'

    @admin.display(description='Verification document')
    def verification_document_link(self, obj):
        if obj.verification_document:
            return format_html(
                '<a href="{}" target="_blank">View verification document</a>',
                obj.verification_document.url,
            )
        return '—'


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_urdu']
    search_fields = ['name', 'name_urdu']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_urdu']
    search_fields = ['name', 'name_urdu']


@admin.register(HifzEducation)
class HifzEducationAdmin(admin.ModelAdmin):
    list_display = ['madrasa_name', 'completion_year', 'teacher_name', 'profile', 'created_at']
    list_filter = ['completion_year']
    search_fields = ['madrasa_name', 'teacher_name', 'profile__full_name']
    raw_id_fields = ['profile']


@admin.register(DarseNizami)
class DarseNizamiAdmin(admin.ModelAdmin):
    list_display = ['madrasa_name', 'wifaq_name', 'sanad_year', 'profile', 'created_at']
    list_filter = ['sanad_year']
    search_fields = ['madrasa_name', 'wifaq_name', 'profile__full_name']
    raw_id_fields = ['profile']


@admin.register(MuftiCourse)
class MuftiCourseAdmin(admin.ModelAdmin):
    list_display = ['madrasa_name', 'takhassus_subject', 'completion_year', 'profile', 'created_at']
    list_filter = ['takhassus_subject', 'completion_year']
    search_fields = ['madrasa_name', 'profile__full_name']
    raw_id_fields = ['profile']


@admin.register(Ijazah)
class IjazahAdmin(admin.ModelAdmin):
    list_display = ['subject', 'ustad_name', 'year', 'profile', 'created_at']
    list_filter = ['year']
    search_fields = ['subject', 'ustad_name', 'profile__full_name']
    raw_id_fields = ['profile']


@admin.register(NazraQirat)
class NazraQiratAdmin(admin.ModelAdmin):
    list_display = ['type', 'qirat_type', 'madrasa_or_teacher', 'completion_year', 'profile', 'created_at']
    list_filter = ['type', 'completion_year']
    search_fields = ['qirat_type', 'madrasa_or_teacher', 'profile__full_name']
    raw_id_fields = ['profile']


@admin.register(AsriEducation)
class AsriEducationAdmin(admin.ModelAdmin):
    list_display = ['level', 'institution', 'year', 'profile', 'created_at']
    list_filter = ['level', 'year']
    search_fields = ['institution', 'profile__full_name']
    raw_id_fields = ['profile']
