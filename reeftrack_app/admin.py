from django.contrib import admin
from .models import UserProfile, SecurityAuditLog

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at', 'updated_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'bio']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25


@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'ip_address', 'created_at']
    list_filter = ['event', 'created_at']
    search_fields = ['user__email', 'ip_address', 'details']
    readonly_fields = ['user', 'event', 'ip_address', 'user_agent', 'details', 'created_at']
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False