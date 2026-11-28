from django.db import models


# 포트폴리오 프로젝트
class Project(models.Model):
    title = models.CharField(max_length=120)
    summary = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    tech = models.CharField(max_length=200, blank=True, default="")
    link = models.CharField(max_length=500, blank=True, default="")  # 카드 클릭 시 이동할 주소(비우면 링크 없음)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    # "React, Django" -> ["React", "Django"] (템플릿에서 태그로 표시)
    @property
    def tech_list(self):
        return [t.strip() for t in self.tech.split(",") if t.strip()]


# 메인 페이지 링크
class SiteLink(models.Model):
    key = models.SlugField(unique=True)
    label = models.CharField(max_length=120)
    url = models.CharField(max_length=500, default="#")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=80, blank=True, default="")

    def __str__(self):
        return self.key + " -> " + self.url
