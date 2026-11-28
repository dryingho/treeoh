from django.urls import path

from . import views

app_name = "uploads"

urlpatterns = [
    path("avatar/", views.upload_avatar, name="avatar"),
    # 업로드한 파일의 '실행'은 별도 주소가 아니라 실제 업로드 주소에서 일어난다:
    #   /media/avatars/<파일>  (config/urls.py 의 serve_avatar 가 처리)
]
