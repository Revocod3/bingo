from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'uuid')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_seller',
                                       'groups', 'user_permissions')}),
        (_('Email verification'), {'fields': ('is_email_verified', 'verification_code', 'verification_code_created_at')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_seller'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_seller', 'is_email_verified', 'uuid')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_seller', 'is_email_verified')
    readonly_fields = ('uuid', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
