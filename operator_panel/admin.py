from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "target", "ip_address")
    list_filter = ("action",)
    search_fields = ("actor", "target", "old_value", "new_value")
