from django.db import models


# 가상 고객 정보 (전부 가짜 데이터)
class DemoCustomer(models.Model):
    name = models.CharField(max_length=80)
    email = models.EmailField(max_length=200)
    phone = models.CharField(max_length=40, blank=True, default="")
    sensitive_memo = models.TextField(blank=True, default="")
    # 평문 비밀번호: 평문 저장이 왜 위험한지 보여주는 용도 (실제 로그인에는 안 씀)
    lab_plaintext_password = models.CharField(max_length=120, blank=True, default="")
    is_virtual = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
