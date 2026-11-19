from django.contrib import admin

from .models import DemoCustomer


@admin.register(DemoCustomer)
class DemoCustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "is_virtual", "created_at")
    search_fields = ("name", "email")
