# 고친(수정) 설정:
#   DJANGO_SETTINGS_MODULE=config.settings.fixed
from .base import *  # noqa

LAB_MODE = "fixed"

# 댓글 자동 이스케이프 유지 -> XSS 막힘
LAB_COMMENTS_RENDER_SAFE = False

# 세션 쿠키 HttpOnly 켬 -> 자바스크립트로 쿠키 못 읽음
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"

# 업로드는 이미지만 + 다시 저장 -> 웹쉘 업로드 막힘
LAB_UPLOAD_VALIDATE_IMAGE = True
LAB_UPLOAD_ALLOWED_EXT = [".png", ".jpg", ".jpeg"]

# 업로드 파일 실행 끔 -> /uploads/run/ 에 접속해도 실행 안 되고 소스만 보임
LAB_RUN_UPLOADS = False

DEBUG = False
