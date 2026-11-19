# 취약 실습 설정. 반드시 직접 골라야 켜진다:
#   DJANGO_SETTINGS_MODULE=config.settings.vulnerable
from .base import *  # noqa

LAB_MODE = "vulnerable"

# 댓글을 그대로 출력한다 -> 저장형 XSS 발생
LAB_COMMENTS_RENDER_SAFE = True

# 세션 쿠키 HttpOnly 끄기.
# 이걸 꺼야 자바스크립트(document.cookie)로 sessionid 를 읽어 세션 탈취가 된다.
# (안 끄면 '강제 요청'형 권한 악용은 되지만 쿠키 탈취는 안 된다.)
SESSION_COOKIE_HTTPONLY = False

# 업로드 검사 끄기 -> .sh 같은 파일도 그냥 올라간다
LAB_UPLOAD_VALIDATE_IMAGE = False
LAB_UPLOAD_ALLOWED_EXT = []

# 업로드한 파일을 Django 가 직접 실행하도록 허용 (/uploads/run/<파일>)
LAB_RUN_UPLOADS = True
