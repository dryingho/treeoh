from django.shortcuts import render

from accounts.models import OperatorProfile
from board.models import Post
from .models import Project, SiteLink


# 메인 페이지
def home(request):
    return render(request, "portfolio/home.html", {
        "profile": OperatorProfile.objects.first(),
        "links": SiteLink.objects.all(),
        "projects": Project.objects.all()[:3],
        # 프런트 페이지는 실제 포트폴리오처럼 보이도록 시나리오 단서 글은 제외한다.
        "recent_posts": Post.objects.filter(is_scenario_clue=False).order_by("-created_at")[:5],
    })


# 소개 페이지
def about(request):
    return render(request, "portfolio/about.html", {"profile": OperatorProfile.objects.first()})


# 프로젝트 목록
def project_list(request):
    return render(request, "portfolio/projects.html", {"projects": Project.objects.all()})
