import getpass
import io
import os
import re
import stat
import subprocess
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve as static_serve

from accounts.models import OperatorProfile
from operator_panel.models import AuditLog
from .models import UploadRecord

# 서버에서 직접 실행하는 확장자
EXECUTABLE_EXTS = [".sh", ".cgi"]


# 업로드한 파일의 접근 주소
def make_run_url(name):
    base = settings.LAB_RUN_BASE_URL.rstrip("/")
    return base + settings.MEDIA_URL + "avatars/" + os.path.basename(name)


# CGI 출력에서 '헤더 블록'과 '본문'을 분리한다.
# 스크립트가 맨 앞에 'Content-Type: ...' 같은 헤더 + 빈 줄을 출력하면(=CGI 응답),
# 그 헤더를 실제 HTTP 응답에 반영할 수 있게 떼어낸다.
# 첫 줄이 'Name: value' 헤더 형태일 때만 헤더로 인정한다(아니면 전체가 본문).
_CGI_HEADER_RE = re.compile(rb"^[A-Za-z][A-Za-z0-9-]*:")


def split_cgi_output(raw):
    if not _CGI_HEADER_RE.match(raw or b""):
        return None, raw
    seps = [(raw.find(s), s) for s in (b"\r\n\r\n", b"\n\n") if raw.find(s) != -1]
    if not seps:
        return None, raw
    idx, sep = min(seps)
    return raw[:idx], raw[idx + len(sep):]


# 접근/실행 기록 남기기
def log_access(text):
    try:
        folder = os.path.join(str(settings.MEDIA_ROOT), "_evidence")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "exec_access.log"), "a", encoding="utf-8") as fp:
            fp.write(text + "\n")
    except Exception:
        pass


@login_required
def upload_avatar(request):
    profile, _ = OperatorProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        f = request.FILES.get("avatar")
        if not f:
            messages.error(request, "파일을 선택하세요.")
            return redirect("uploads:avatar")

        ext = os.path.splitext(f.name)[1].lower()

        if settings.LAB_UPLOAD_VALIDATE_IMAGE:
            # 이미지인지 확인하고 다시 저장한다
            if ext not in settings.LAB_UPLOAD_ALLOWED_EXT:
                messages.error(request, "이미지 파일만 올릴 수 있어요.")
                return redirect("uploads:avatar")
            from PIL import Image
            try:
                img = Image.open(f)
                img.verify()
                f.seek(0)
                img = Image.open(f).convert("RGB")
            except Exception:
                messages.error(request, "이미지로 열 수 없는 파일이에요.")
                return redirect("uploads:avatar")
            buf = io.BytesIO()
            fmt = "PNG" if ext == ".png" else "JPEG"
            img.save(buf, format=fmt)
            new_name = "avatar.png" if fmt == "PNG" else "avatar.jpg"
            profile.avatar.save(new_name, ContentFile(buf.getvalue()), save=True)
            is_exec = False
        else:
            # 검사 없이 그대로 저장한다
            profile.avatar.save(f.name, f, save=True)
            is_exec = ext in EXECUTABLE_EXTS

        stored = os.path.basename(profile.avatar.name)
        rec = UploadRecord.objects.create(
            operator=request.user.username,
            original_name=f.name,
            stored_name=stored,
            content_type=getattr(f, "content_type", ""),
            size=f.size,
            served_url=make_run_url(stored),
            is_executable_candidate=is_exec,
        )
        AuditLog.objects.create(
            actor=request.user.username, action="avatar_upload",
            target=stored, new_value=rec.served_url,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        if is_exec:
            messages.warning(request, "저장됨. 이 파일은 서버에서 실행될 수 있어요: " + rec.served_url)
        else:
            messages.success(request, "프로필 사진이 업로드되었습니다.")
        return redirect("uploads:avatar")

    return render(request, "uploads/upload.html", {
        "profile": profile,
        "records": UploadRecord.objects.filter(operator=request.user.username)[:10],
        "validate_on": settings.LAB_UPLOAD_VALIDATE_IMAGE,
        "run_base": settings.LAB_RUN_BASE_URL,
    })


# /media/avatars/<파일> 요청 처리.
# - 이미지 등: 올바른 타입으로 정적 서빙.
# - .sh/.cgi: LAB_RUN_UPLOADS 가 켜져 있으면 파일 자신을 CGI 방식으로 실행하고
#   (shebang 이 인터프리터를 결정), 꺼져 있으면 소스만 보여준다.
# CGI 처리 특성상 CSRF 검증 대상이 아니다(토큰 없이 POST 되어야 한다).
@csrf_exempt
def serve_avatar(request, name):
    base = os.path.basename(name)  # 경로 이탈 방지
    ext = os.path.splitext(base)[1].lower()
    path = os.path.join(str(settings.MEDIA_ROOT), "avatars", base)

    # 실행 대상이 아니면(이미지 등) 그대로 정적 서빙
    if ext not in EXECUTABLE_EXTS:
        return static_serve(request, "avatars/" + base, document_root=str(settings.MEDIA_ROOT))

    if not os.path.isfile(path):
        return HttpResponse("파일 없음", status=404)

    now = datetime.now().isoformat()
    log_access(now + "\tGET\t" + base)

    # 실행하지 않고 소스만 보여준다
    if not settings.LAB_RUN_UPLOADS:
        with open(path, encoding="utf-8", errors="replace") as fp:
            return HttpResponse("[실행 차단됨]\n\n" + fp.read(),
                                content_type="text/plain; charset=utf-8")

    # 파일 자신을 하나의 프로그램으로 실행한다.
    log_access(now + "\tEXEC\t" + base + "\tuser=" + getpass.getuser())
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    # 업로드 실행물(웹셸 포함)에 넘길 환경변수는 '최소 화이트리스트'로만 구성한다.
    # os.environ 전체를 넘기면 .env 에서 적재된 비밀(DJANGO_SECRET_KEY 등)이
    # 웹셸의 `env`/`printenv` 로 그대로 새어나가므로, 실행에 꼭 필요한 값만 전달한다.
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LAB_EXEC_DOCROOT": str(settings.MEDIA_ROOT),
        # 실행 스크립트에 DB 파일 경로를 환경변수로 전달한다(의도된 유출 경로).
        "LAB_LEAK_DB_NAME": str(settings.DATABASES["default"].get("NAME", "")),
        # CGI 스타일 입력: GET 은 QUERY_STRING, POST 는 본문을 stdin 으로 전달한다.
        "QUERY_STRING": request.META.get("QUERY_STRING", ""),
        "REQUEST_METHOD": request.method,
        "CONTENT_TYPE": request.META.get("CONTENT_TYPE", ""),
    }
    body_in = request.body or b""
    env["CONTENT_LENGTH"] = str(len(body_in))
    try:
        # ["bash", path] 가 아니라 [path] — 파일의 shebang 이 인터프리터를 정한다.
        result = subprocess.run([path], input=body_in, capture_output=True, timeout=15,
                                cwd=str(settings.MEDIA_ROOT), env=env)
    except Exception as e:
        return HttpResponse("[실행 오류] " + str(e),
                            content_type="text/plain; charset=utf-8")

    raw = result.stdout
    header_block, body = split_cgi_output(raw)
    if header_block is not None:
        # CGI 응답: 스크립트가 낸 Content-Type 을 실제 응답에 반영하고 '본문만' 돌려준다.
        # (헤더 줄이 본문에 섞이지 않아 브라우저가 HTML 로 렌더링한다. stderr 는 응답에 넣지 않음.)
        content_type = "text/plain; charset=utf-8"
        for line in header_block.split(b"\n"):
            if line.lower().startswith(b"content-type:"):
                value = line.split(b":", 1)[1].strip().decode("latin-1")
                if value:
                    content_type = value
        # text/* 인데 charset 이 없으면 UTF-8 로 보정한다(한글 깨짐 방지).
        if content_type.lower().startswith("text/") and "charset=" not in content_type.lower():
            content_type += "; charset=utf-8"
        return HttpResponse(body, content_type=content_type)

    # CGI 헤더가 없는 스크립트(.sh 등)는 기존처럼 stdout(+stderr)을 평문으로 보여준다.
    out = raw.decode("utf-8", "replace")
    if result.stderr:
        out += "\n[에러]\n" + result.stderr.decode("utf-8", "replace")
    return HttpResponse(out, content_type="text/plain; charset=utf-8")
