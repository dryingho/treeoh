from django.db import models


# 업로드된 파일 기록 (파일을 저장했다는 증거)
class UploadRecord(models.Model):
    operator = models.CharField(max_length=80, blank=True, default="")
    original_name = models.CharField(max_length=255)
    stored_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True, default="")
    size = models.PositiveIntegerField(default=0)
    served_url = models.CharField(max_length=600, blank=True, default="")   # 실행 서비스 주소
    is_executable_candidate = models.BooleanField(default=False)            # .sh 처럼 실행될 수 있는 파일인지
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_name
