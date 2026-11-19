from django.db import models


# 공격자 수집기(로컬 모의)가 받은 쿠키 기록
class CollectorHit(models.Model):
    received_at = models.DateTimeField(auto_now_add=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True, default="")
    referer = models.CharField(max_length=500, blank=True, default="")
    raw_cookie = models.TextField(blank=True, default="")
    note = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return "쿠키수신 " + str(self.id)

    # 쿠키에 sessionid 가 들어있는지
    @property
    def has_sessionid(self):
        return "sessionid=" in self.raw_cookie
