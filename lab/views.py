import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from board.models import Comment, Post
from demo_records.models import DemoCustomer
from operator_panel.models import AuditLog
from portfolio.models import SiteLink
from uploads.models import UploadRecord
from .models import CollectorHit


# 공격자 수집기(로컬 모의) - 받은 쿠키를 저장한다
@csrf_exempt
def collector(request):
    cookie = request.GET.get("c") or request.POST.get("c") or ""
    CollectorHit.objects.create(
        source_ip=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        referer=request.META.get("HTTP_REFERER", "")[:500],
        raw_cookie=cookie[:4000],
        note="로컬 모의 수집기",
    )
    # 파일로도 남긴다
    try:
        log = str(settings.LAB_COLLECTOR_LOG)
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "a", encoding="utf-8") as fp:
            fp.write(timezone.now().isoformat() + "\t" + cookie + "\n")
    except Exception:
        pass
    return HttpResponse("ok")


# 실습 상태 보기 (공격을 하는 게 아니라 흔적만 보여준다)
def status(request):
    evidence_dir = os.path.join(str(settings.MEDIA_ROOT), "_evidence")
    evidence_files = []
    if os.path.isdir(evidence_dir):
        evidence_files = [f for f in sorted(os.listdir(evidence_dir)) if not f.startswith(".")]

    # 스크립트처럼 보이는 댓글 수 세기
    script_comments = 0
    for c in Comment.objects.all():
        if c.looks_like_script:
            script_comments += 1

    # sessionid 가 들어온 수집 건수 세기
    session_hits = 0
    for h in CollectorHit.objects.all():
        if h.has_sessionid:
            session_hits += 1

    data = {
        "mode": settings.LAB_MODE,
        "flags": {
            "LAB_COMMENTS_RENDER_SAFE": settings.LAB_COMMENTS_RENDER_SAFE,
            "SESSION_COOKIE_HTTPONLY": settings.SESSION_COOKIE_HTTPONLY,
            "LAB_UPLOAD_VALIDATE_IMAGE": settings.LAB_UPLOAD_VALIDATE_IMAGE,
            "LAB_UPLOAD_ALLOWED_EXT": settings.LAB_UPLOAD_ALLOWED_EXT,
        },
        "counts": {
            "posts": Post.objects.count(),
            "comments": Comment.objects.count(),
            "comments_script_like": script_comments,
            "defaced_links": SiteLink.objects.filter(is_defaced=True).count(),
            "upload_exec_candidates": UploadRecord.objects.filter(is_executable_candidate=True).count(),
            "collector_hits": CollectorHit.objects.count(),
            "collector_hits_with_sessionid": session_hits,
            "demo_customers": DemoCustomer.objects.count(),
            "audit_logs": AuditLog.objects.count(),
        },
        "evidence_files": evidence_files,
    }
    if request.GET.get("format") == "json":
        return JsonResponse(data)
    return render(request, "lab/status.html", {"data": data})
