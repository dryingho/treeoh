from django.contrib import admin

from .models import CollectorHit


@admin.register(CollectorHit)
class CollectorHitAdmin(admin.ModelAdmin):
    list_display = ("received_at", "source_ip", "has_sessionid", "note")
    search_fields = ("raw_cookie", "source_ip")
