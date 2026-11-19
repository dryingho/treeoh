# 공통 설정. 이 파일만 쓰면 '안전한 기본값'으로 동작한다.
# 취약 동작은 vulnerable.py, 고친 동작은 fixed.py 에서만 켠다.
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# 프로젝트 최상위 폴더
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "lab-insecure-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 우리 앱
    "accounts",
    "portfolio",
    "board",
    "operator_panel",
    "uploads",
    "demo_records",
    "lab",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "lab.context_processors.lab_banner",   # 상단 배너용 공통 값
            ],
        },
    },
]

# 데이터베이스 (PostgreSQL). 앱은 전체 권한 계정(lab_admin)으로 접속.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "portfolio_lab"),
        "USER": os.environ.get("POSTGRES_USER", "lab_admin"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "lab_admin_pw_change_me"),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# 로그인 비밀번호는 Django 기본 해시(PBKDF2)를 그대로 쓴다.
AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# 정적 파일 / 업로드 (외부 CDN 안 씀)
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("LAB_MEDIA_ROOT", BASE_DIR / "shared" / "uploads"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/operator/login/"

# 세션 쿠키: 기본은 안전(HttpOnly 켬). vulnerable.py 에서만 끈다.
SESSION_COOKIE_HTTPONLY = True

# ===== 실습 켜고 끄는 스위치 (기본값은 안전) =====
LAB_MODE = "base"
LAB_COMMENTS_RENDER_SAFE = False          # True 면 댓글을 그대로 출력 -> XSS
LAB_UPLOAD_VALIDATE_IMAGE = True          # True 면 이미지 검사/재저장
LAB_UPLOAD_ALLOWED_EXT = [".png", ".jpg", ".jpeg", ".gif"]

# 업로드한 파일을 Django 가 직접 실행하는 주소의 베이스
LAB_RUN_BASE_URL = os.environ.get("LAB_RUN_BASE_URL", "http://localhost:8000")
# True 면 /uploads/run/<파일> 에 접속할 때 서버에서 진짜로 실행한다 (취약).
LAB_RUN_UPLOADS = False

# 유출용 최소 권한 DB 계정 (실행된 스크립트가 DB 범위를 확인할 때 씀)
LAB_LEAK_DB_USER = os.environ.get("LAB_LEAK_DB_USER", "app_legacy")
LAB_LEAK_DB_PASSWORD = os.environ.get("LAB_LEAK_DB_PASSWORD", "legacy_pw_exposed_in_git_2019")

LAB_COLLECTOR_LOG = BASE_DIR / "lab_collector" / "stolen_cookies.log"

LAB_WARNING = "⚠️ 교육용으로 일부러 취약하게 만든 환경입니다. 실제 서비스/인물과 무관."
