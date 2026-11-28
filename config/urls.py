from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from uploads import views as uploads_views

urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("admin/", admin.site.urls),
    path("", include("portfolio.urls")),           # 소개/메인
    path("board/", include("board.urls")),         # 게시판/게시글/댓글
    path("operator/", include("operator_panel.urls")),  # 운영자 화면
    path("uploads/", include("uploads.urls")),     # 프로필 사진 업로드
]

# 아바타 파일은 전용 뷰로 서빙 (아래 static() 보다 먼저 와야 한다)
urlpatterns += [path("media/avatars/<str:name>", uploads_views.serve_avatar)]

# 미디어/정적 파일 서빙 (개발용)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
