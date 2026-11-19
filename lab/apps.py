from django.apps import AppConfig


class LabConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lab"
    verbose_name = "랩(초기화/상태/수집기)"
