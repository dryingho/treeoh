from django.contrib import admin

from .models import Project, SiteLink


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "tech", "order")
    ordering = ("order",)


@admin.register(SiteLink)
class SiteLinkAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "url", "is_defaced", "updated_at", "updated_by")
    list_filter = ("is_defaced",)
