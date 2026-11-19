from django.contrib import admin

from .models import OperatorProfile


@admin.register(OperatorProfile)
class OperatorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "updated_at")
