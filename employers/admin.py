from django.contrib import admin
from django.utils.html import format_html

from .models import Employer


@admin.action(description='Mark selected employers as verified')
def mark_as_verified(modeladmin, request, queryset):
    updated = queryset.update(verification_status=Employer.VerificationStatus.VERIFIED)
    modeladmin.message_user(request, f'{updated} employer(s) marked as verified.')


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = [
        'organization_name',
        'organization_type',
        'contact_person',
        'city',
        'verification_status',
        'created_by_admin',
        'created_at',
    ]
    list_filter = ['verification_status', 'organization_type', 'province', 'created_by_admin']
    search_fields = ['organization_name', 'contact_person']
    raw_id_fields = ['user', 'province', 'city', 'district', 'village']
    readonly_fields = [
        'created_at',
        'updated_at',
        'verification_document_link',
    ]
    actions = [mark_as_verified]

    fieldsets = (
        (None, {
            'fields': (
                'user',
                'organization_type',
                'organization_name',
                'description',
                'contact_person',
            ),
        }),
        ('Location', {
            'fields': ('province', 'city', 'district', 'village'),
        }),
        ('Contact', {
            'fields': ('whatsapp_number', 'contact_phone', 'contact_email'),
        }),
        ('Verification', {
            'fields': (
                'verification_status',
                'verification_document',
                'verification_document_link',
                'created_by_admin',
                'admin_notes',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Verification document')
    def verification_document_link(self, obj):
        if obj.verification_document:
            return format_html(
                '<a href="{}" target="_blank">View verification document</a>',
                obj.verification_document.url,
            )
        return '—'
