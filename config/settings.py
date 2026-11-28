# 설정 단일 파일. 안전/취약 모드는 LAB_MODE 환경변수 하나로 갈린다.
#   LAB_MODE=safe (기본)  -> python manage.py runserver  => 안전 모드
#   LAB_MODE=vulnerable   -> python manage.py runserver  => 취약 모드
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# 프로젝트 최상위 폴더 (이 파일은 config/settings.py 이므로 두 단계 위)
BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY: 세션 쿠키·토큰 서명에 사용. 운영 환경에서는 환경변수로 주입한다.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-lab-2019-committed-by-mistake")

# DB 민감 필드(연락 메모·실습 비밀번호) 암호화 키 (Fernet).
# 운영이라면 환경변수/시크릿 매니저로 주입해야 하지만, 이 랩은 '과거 Git 커밋에 그대로
# 올라간' 값을 기본값으로 둔다(= Git 이력 유출 시나리오의 '보물'). 이 키가 있으면
# db.sqlite3 에 담긴 암호문을 전부 복호화할 수 있다.
LAB_DB_ENC_KEY = os.environ.get("LAB_DB_ENC_KEY", "Sz1G86BggdW3YmVTFAMnYpQPKq0Ekl1ivn-QjMhJ_SA=")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,treeoh.dryingho.com").split(",")

# CSRF: POST 요청(로그인 등)을 신뢰할 출처. scheme(https/http)까지 포함해야 한다.
# 커스텀 도메인이나 HTTPS 로 접속하면 이 목록에 없을 때 403(CSRF 검증 실패)이 난다.
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://treeoh.dryingho.com,http://treeoh.dryingho.com",
).split(",")

# 리버스 프록시가 HTTPS 를 종단하고 X-Forwarded-Proto 를 넘겨줄 때,
# Django 가 원 요청이 HTTPS 였음을 알도록 한다(CSRF/보안 쿠키 판단에 사용).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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

# 데이터베이스: SQLite 파일 하나. 별도 DB 서버/계정 없음.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("LAB_SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
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

# 세션 저장 방식: 서명 쿠키 (SECRET_KEY 로 서명)
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# ===== 실행 모드: 환경변수 LAB_MODE 하나로 안전/취약을 가른다 =====
#   safe(기본): XSS 방지 · 쿠키 HttpOnly · 업로드 이미지 검사 · 업로드 실행 차단
#   vulnerable: 위 네 가지를 모두 취약하게 켠다
_mode = os.environ.get("LAB_MODE", "safe").strip().lower()
_VULNERABLE = _mode in ("vulnerable", "vuln", "unsafe", "on", "1")
LAB_MODE = "vulnerable" if _VULNERABLE else "safe"

# 세션 쿠키 HttpOnly: 안전=True / 취약=False(=document.cookie 로 세션 탈취 가능)
SESSION_COOKIE_HTTPONLY = not _VULNERABLE

# 댓글 출력: 안전=이스케이프 / 취약=원문 그대로(=저장형 XSS)
LAB_COMMENTS_RENDER_SAFE = _VULNERABLE

# 업로드 검사: 안전=이미지 검사·재저장 / 취약=검사 없음
LAB_UPLOAD_VALIDATE_IMAGE = not _VULNERABLE
LAB_UPLOAD_ALLOWED_EXT = [] if _VULNERABLE else [".png", ".jpg", ".jpeg", ".gif"]

# 업로드 파일 실행: 안전=차단(소스만 표시) / 취약=파일 자신을 실행(RCE)
LAB_RUN_UPLOADS = _VULNERABLE

# 업로드 파일 주소를 만들 때 쓰는 베이스 (보통 Django 주소와 동일)
LAB_RUN_BASE_URL = os.environ.get("LAB_RUN_BASE_URL", "http://localhost:8000")

LAB_WARNING = "⚠️ 교육용으로 일부러 취약하게 만든 환경입니다. 실제 서비스/인물과 무관."
