from django.apps import AppConfig


class DemoRecordsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "demo_records"
    verbose_name = "가상 고객 데이터(실습)"
