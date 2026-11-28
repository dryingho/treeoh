from django.conf import settings
from django.db import models


# 운영자 프로필 (소개글 + 프로필 사진)
class OperatorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=80, default="운영자")
    bio = models.TextField(blank=True, default="")
    # 아바타는 FileField (이미지 외 파일도 저장 가능)
    avatar = models.FileField(upload_to="avatars/", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    # 사진 주소 만들기
    @property
    def avatar_url(self):
        if self.avatar:
            return settings.MEDIA_URL + str(self.avatar)
        return ""
