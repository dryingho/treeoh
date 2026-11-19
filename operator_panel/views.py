from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import OperatorProfile
from portfolio.models import SiteLink
from .models import AuditLog


# 활동 기록 저장하기
def save_log(request, action, target="", old="", new=""):
    AuditLog.objects.create(
        actor=getattr(request.user, "username", ""),
        action=action, target=target, old_value=old, new_value=new,
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
    )


# 운영자 로그인
def operator_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            save_log(request, "login", username)
            return redirect("operator:dashboard")
        save_log(request, "login_failed", username)
        messages.error(request, "로그인 실패: 아이디/비밀번호를 확인하세요.")
    return render(request, "operator_panel/login.html")


def operator_logout(request):
    logout(request)
    return redirect("portfolio:home")


# 운영자 메인 화면
@login_required
def dashboard(request):
    profile, _ = OperatorProfile.objects.get_or_create(user=request.user)
    return render(request, "operator_panel/dashboard.html", {
        "profile": profile,
        "links": SiteLink.objects.all(),
        "recent_audit": AuditLog.objects.all()[:10],
    })


# 소개글 수정
@login_required
def edit_profile(request):
    profile, _ = OperatorProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        old = profile.bio
        profile.display_name = request.POST.get("display_name") or profile.display_name
        profile.bio = request.POST.get("bio", profile.bio)
        profile.save()
        save_log(request, "profile_update", "profile", old, profile.bio)
        messages.success(request, "저장되었습니다.")
        return redirect("operator:dashboard")
    return render(request, "operator_panel/edit_profile.html", {"profile": profile})


# 메인 링크 수정 (여기가 변조되는 곳)
@login_required
def edit_links(request):
    if request.method == "POST":
        link = get_object_or_404(SiteLink, key=request.POST.get("key", ""))
        old_url = link.url
        if link.original_url == "":
            link.original_url = old_url
        link.url = request.POST.get("url", "")
        # 정상 로그인한 운영자가 링크를 바꾸는 것은 '변조'가 아니다.
        # 링크가 업로드 실행 주소(/uploads/run/)로 바뀐 경우만 변조로 표시한다
        # (공격 시나리오 A: XSS 강제 요청으로 웹쉘 주소로 바뀌는 상황).
        link.is_defaced = "/uploads/run/" in link.url
        link.updated_by = request.user.username
        link.save()
        save_log(request, "link_change", link.key, old_url, link.url)
        messages.success(request, "링크가 변경되었습니다.")
        return redirect("operator:dashboard")
    return render(request, "operator_panel/edit_links.html", {"links": SiteLink.objects.all()})


# 활동 기록 보기
@login_required
def audit_log(request):
    return render(request, "operator_panel/audit.html", {"logs": AuditLog.objects.all()[:200]})
