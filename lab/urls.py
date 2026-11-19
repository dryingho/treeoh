from django.urls import path

from . import views

app_name = "lab"

urlpatterns = [
    # [모의] 공격자 로컬 수집기
    path("collector/", views.collector, name="collector"),
    # 시연 상태 확인 (공격 스킵 아님)
    path("status/", views.status, name="status"),
]
