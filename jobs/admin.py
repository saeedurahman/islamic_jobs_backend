from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import JobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer_link', 'category', 'city', 'status', 'created_at']
    list_filter = ['status', 'category', 'province', 'experience_required']
    search_fields = ['title', 'description']
    raw_id_fields = ['employer', 'province', 'city', 'district']
    filter_horizontal = ['required_languages']
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Employer')
    def employer_link(self, obj):
        url = reverse('admin:employers_employer_change', args=[obj.employer_id])
        return format_html('<a href="{}">{}</a>', url, obj.employer)
