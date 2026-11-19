import getpass
import io
import os
import subprocess
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import redirect, render

from accounts.models import OperatorProfile
from operator_panel.models import AuditLog
from .models import UploadRecord

# Django 가 직접 실행하는(=취약) 확장자
EXECUTABLE_EXTS = [".sh", ".cgi"]


# 업로드한 파일을 실행하는 주소 만들기
def make_run_url(name):
    base = settings.LAB_RUN_BASE_URL.rstrip("/")
    return base + "/uploads/run/" + os.path.basename(name)


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
            # 수정 모드: 이미지인지 확인하고 다시 저장한다 (숨긴 코드 제거)
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
            # 취약 모드: 검사 없이 그대로 저장한다
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


# 업로드한 파일을 Django 가 직접 실행한다 (일부러 만든 취약 기능).
# 취약 모드(LAB_RUN_UPLOADS=True)에서만 실행되고, 수정 모드에선 소스만 보여준다.
def run_file(request, name):
    base = os.path.basename(name)  # 경로 이탈 방지
    path = os.path.join(str(settings.MEDIA_ROOT), "avatars", base)
    now = datetime.now().isoformat()
    log_access(now + "\tGET\t" + base)

    if not os.path.isfile(path):
        return HttpResponse("파일 없음", status=404)

    ext = os.path.splitext(base)[1].lower()

    # 실행 대상이 아니면 그냥 파일 내용만 보여준다
    if ext not in EXECUTABLE_EXTS:
        with open(path, "rb") as fp:
            return HttpResponse(fp.read())

    # 수정 모드: 실행하지 않고 소스만
    if not settings.LAB_RUN_UPLOADS:
        with open(path, encoding="utf-8", errors="replace") as fp:
            return HttpResponse("[실행 차단됨]\n\n" + fp.read(),
                                content_type="text/plain; charset=utf-8")

    # 취약 모드: 진짜로 실행
    log_access(now + "\tEXEC\t" + base + "\tuser=" + getpass.getuser())
    env = dict(os.environ)
    env["LAB_EXEC_DOCROOT"] = str(settings.MEDIA_ROOT)
    env["LAB_LEAK_DB_HOST"] = settings.DATABASES["default"]["HOST"]
    env["LAB_LEAK_DB_NAME"] = settings.DATABASES["default"]["NAME"]
    env["LAB_LEAK_DB_USER"] = settings.LAB_LEAK_DB_USER
    env["LAB_LEAK_DB_PASSWORD"] = settings.LAB_LEAK_DB_PASSWORD
    try:
        result = subprocess.run(["bash", path], capture_output=True, timeout=15,
                                cwd=str(settings.MEDIA_ROOT), env=env)
        out = result.stdout.decode("utf-8", "replace")
        if result.stderr:
            out += "\n[에러]\n" + result.stderr.decode("utf-8", "replace")
    except Exception as e:
        out = "[실행 오류] " + str(e)
    return HttpResponse(out, content_type="text/plain; charset=utf-8")
