from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'applicant', 'status', 'applied_at']
    list_filter = ['status']
    search_fields = ['job__title', 'applicant__full_name']
    readonly_fields = ('job', 'applicant', 'status', 'cover_note', 'applied_at', 'status_updated_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
