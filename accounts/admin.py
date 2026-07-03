from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email',
        'phone_number',
        'user_role',
        'is_phone_verified',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'created_at',
    ]
    list_filter = ['user_role', 'is_phone_verified', 'is_staff', 'is_active']
    search_fields = ['email', 'phone_number', 'first_name', 'last_name', 'username']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            'Islamic Jobs Profile',
            {
                'fields': (
                    'phone_number',
                    'user_role',
                    'is_phone_verified',
                    'created_at',
                ),
            },
        ),
    )
    readonly_fields = ['created_at']
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            'Islamic Jobs Profile',
            {
                'fields': (
                    'email',
                    'phone_number',
                    'user_role',
                    'is_phone_verified',
                ),
            },
        ),
    )
