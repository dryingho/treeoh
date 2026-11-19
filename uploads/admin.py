from django.contrib import admin

from .models import UploadRecord


@admin.register(UploadRecord)
class UploadRecordAdmin(admin.ModelAdmin):
    list_display = ("original_name", "stored_name", "operator", "is_executable_candidate",
                    "size", "uploaded_at")
    list_filter = ("is_executable_candidate",)
    search_fields = ("original_name", "stored_name", "operator")
