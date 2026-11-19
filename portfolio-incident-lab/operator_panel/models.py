from django.db import models


# 운영자 활동 기록 (조사할 때 보는 로그)
class AuditLog(models.Model):
    ACTIONS = [
        ("link_change", "사이트 링크 변경"),
        ("profile_update", "프로필 수정"),
        ("login", "로그인"),
        ("login_failed", "로그인 실패"),
        ("avatar_upload", "프로필 사진 업로드"),
    ]
    actor = models.CharField(max_length=80, blank=True, default="")
    action = models.CharField(max_length=40, choices=ACTIONS)
    target = models.CharField(max_length=120, blank=True, default="")
    old_value = models.TextField(blank=True, default="")
    new_value = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.action + " / " + self.actor
