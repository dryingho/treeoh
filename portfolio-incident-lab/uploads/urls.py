from django.urls import path

from . import views

app_name = "uploads"

urlpatterns = [
    path("avatar/", views.upload_avatar, name="avatar"),
    # 업로드한 파일을 Django 가 직접 실행하는 주소 (취약 모드에서만 실행)
    path("run/<str:name>", views.run_file, name="run"),
]
