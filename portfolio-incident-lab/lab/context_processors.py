from django.conf import settings


# 모든 페이지에서 쓰는 공통 값 (상단 배너 등)
def lab_banner(request):
    return {
        "LAB_MODE": settings.LAB_MODE,
        "LAB_WARNING": settings.LAB_WARNING,
        "LAB_COMMENTS_RENDER_SAFE": settings.LAB_COMMENTS_RENDER_SAFE,
        "LAB_RUN_BASE_URL": settings.LAB_RUN_BASE_URL,
        "SESSION_COOKIE_HTTPONLY": settings.SESSION_COOKIE_HTTPONLY,
    }
