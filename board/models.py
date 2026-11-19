from django.db import models


# 게시글
class Post(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, default="")
    author_name = models.CharField(max_length=80, default="익명")
    is_notice = models.BooleanField(default=False)
    is_scenario_clue = models.BooleanField(default=False)  # 사고 발견용 단서 글
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_notice", "-created_at"]

    def __str__(self):
        return self.title


# 댓글 (이 내용이 저장형 XSS 가 된다)
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author_name = models.CharField(max_length=80, default="익명")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True, default="")

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return "댓글 " + str(self.id)

    # 스크립트처럼 보이는 댓글인지 (조사할 때 사용)
    @property
    def looks_like_script(self):
        t = self.body.lower()
        return "<script" in t or "onerror=" in t or "onload=" in t or "javascript:" in t
