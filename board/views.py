from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import Comment, Post


# 게시글 목록
def post_list(request):
    return render(request, "board/post_list.html", {"posts": Post.objects.all()})


# 게시글 + 댓글 보기
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, "board/post_detail.html", {
        "post": post,
        "comments": post.comments.all(),
        # 이 값이 True 면 댓글을 그대로 출력해서 XSS 가 터진다
        "lab_render_safe": settings.LAB_COMMENTS_RENDER_SAFE,
    })


# 댓글 등록
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        author = request.POST.get("author_name") or "익명"
        body = request.POST.get("body") or ""
        if body.strip() == "":
            messages.error(request, "댓글 내용을 입력하세요.")
        else:
            # 입력을 그대로 저장한다 (일부러 안전 처리 안 함)
            Comment.objects.create(
                post=post,
                author_name=author[:80],
                body=body,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
            )
            messages.success(request, "댓글이 등록되었습니다.")
    return redirect("board:detail", pk=pk)
