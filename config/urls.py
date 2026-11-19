from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),               # Django 기본 admin (요구사항: 별도)
    path("", include("portfolio.urls")),           # 소개/프로젝트/메인
    path("board/", include("board.urls")),         # 게시판/게시글/댓글
    path("operator/", include("operator_panel.urls")),  # /operator/ 운영자 화면
    path("uploads/", include("uploads.urls")),     # 프로필 사진 업로드
    path("records/", include("demo_records.urls")),# 가상 고객 데이터(열람 제한)
    path("lab/", include("lab.urls")),             # 수집기(모의)/상태/증거
]

# 로컬 VM 에서 Django 가 미디어(업로드)를 직접 서빙(개발용).
# 주의: Django 는 이 파일을 '실행'하지 않고 '정적 서빙'만 한다. 실제 실행은 별도 실행 서비스.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
