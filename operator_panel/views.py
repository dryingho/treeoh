from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import OperatorProfile
from portfolio.models import Project, SiteLink
from .models import AuditLog


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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


# 메인 링크 수정
@login_required
def edit_links(request):
    if request.method == "POST":
        link = get_object_or_404(SiteLink, key=request.POST.get("key", ""))
        old_url = link.url
        link.url = request.POST.get("url", "")
        link.updated_by = request.user.username
        link.save()
        save_log(request, "link_change", link.key, old_url, link.url)
        messages.success(request, "링크가 변경되었습니다.")
        return redirect("operator:dashboard")
    return render(request, "operator_panel/edit_links.html", {"links": SiteLink.objects.all()})


# 대표 프로젝트(홈 미리보기) 수정
@login_required
def edit_projects(request):
    if request.method == "POST":
        form_action = request.POST.get("form_action", "save")
        if form_action == "add":
            p = Project.objects.create(
                title=(request.POST.get("title") or "새 프로젝트").strip(),
                summary=request.POST.get("summary", "").strip(),
                tech=request.POST.get("tech", "").strip(),
                link=request.POST.get("link", "").strip(),
                order=_to_int(request.POST.get("order"), 0),
            )
            save_log(request, "project_update", "project:%s" % p.id, "", "추가: %s" % p.title)
            messages.success(request, "프로젝트가 추가되었습니다.")
        elif form_action == "delete":
            p = get_object_or_404(Project, pk=request.POST.get("id"))
            title = p.title
            p.delete()
            save_log(request, "project_update", "project", title, "삭제됨")
            messages.success(request, "프로젝트가 삭제되었습니다.")
        else:
            p = get_object_or_404(Project, pk=request.POST.get("id"))
            old = "%s | %s | %s | %s | order=%s" % (p.title, p.summary, p.tech, p.link, p.order)
            p.title = (request.POST.get("title", p.title) or p.title).strip()
            p.summary = request.POST.get("summary", p.summary)
            p.tech = request.POST.get("tech", p.tech)
            p.link = request.POST.get("link", p.link)
            p.order = _to_int(request.POST.get("order"), p.order)
            p.save()
            new = "%s | %s | %s | %s | order=%s" % (p.title, p.summary, p.tech, p.link, p.order)
            save_log(request, "project_update", "project:%s" % p.id, old, new)
            messages.success(request, "저장되었습니다.")
        return redirect("operator:edit_projects")
    return render(request, "operator_panel/edit_projects.html", {"projects": Project.objects.all()})


# 활동 기록 보기
@login_required
def audit_log(request):
    return render(request, "operator_panel/audit.html", {"logs": AuditLog.objects.all()[:200]})
