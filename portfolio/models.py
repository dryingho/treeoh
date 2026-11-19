from django.db import models


# 포트폴리오 프로젝트
class Project(models.Model):
    title = models.CharField(max_length=120)
    summary = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    tech = models.CharField(max_length=200, blank=True, default="")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    # "React, Django" -> ["React", "Django"] (템플릿에서 태그로 표시)
    @property
    def tech_list(self):
        return [t.strip() for t in self.tech.split(",") if t.strip()]


# 메인 페이지 링크 (공격 때 주소가 바뀌는 대상)
class SiteLink(models.Model):
    key = models.SlugField(unique=True)
    label = models.CharField(max_length=120)
    url = models.CharField(max_length=500, default="#")
    original_url = models.CharField(max_length=500, blank=True, default="")  # 원래 주소
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=80, blank=True, default="")
    is_defaced = models.BooleanField(default=False)  # 변조됐는지

    def __str__(self):
        return self.key + " -> " + self.url
