from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import OperatorProfile
from .models import Comment, Post


# 게시글 목록
def post_list(request):
    return render(request, "board/post_list.html", {"posts": Post.objects.all()})


# 글쓰기 (운영자만)
@login_required
def create_post(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        body = request.POST.get("body") or ""
        if title == "":
            messages.error(request, "제목을 입력하세요.")
        else:
            # 글쓴이 이름은 운영자 표시 이름(프로필에서 변경 가능)을 쓴다.
            profile, _ = OperatorProfile.objects.get_or_create(user=request.user)
            author = profile.display_name or request.user.username
            post = Post.objects.create(
                title=title[:200],
                body=body,
                author_name=author,
                is_notice=bool(request.POST.get("is_notice")),
            )
            messages.success(request, "글이 등록되었습니다.")
            return redirect("board:detail", pk=post.pk)
    return render(request, "board/post_form.html")


# 게시글 삭제 (운영자만)
@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        post.delete()
        messages.success(request, "글을 삭제했습니다.")
        return redirect("board:list")
    return redirect("board:detail", pk=pk)


# 댓글 삭제 (운영자만)
@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post_id
    if request.method == "POST":
        comment.delete()
        messages.success(request, "댓글을 삭제했습니다.")
    return redirect("board:detail", pk=post_pk)


# 게시글 + 댓글 보기
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, "board/post_detail.html", {
        "post": post,
        "comments": post.comments.all(),
        # 댓글 원문 그대로 출력 여부
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
            # 입력을 그대로 저장한다
            Comment.objects.create(
                post=post,
                author_name=author[:80],
                body=body,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
            )
            messages.success(request, "댓글이 등록되었습니다.")
    return redirect("board:detail", pk=pk)
