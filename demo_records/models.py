from django.db import models

from .fields import EncryptedTextField


# 가상 고객 정보 (전부 가짜 데이터)
class DemoCustomer(models.Model):
    name = models.CharField(max_length=80)
    email = models.EmailField(max_length=200)
    phone = models.CharField(max_length=40, blank=True, default="")
    # 민감 필드: DB(db.sqlite3)에는 Fernet '암호문'으로 저장된다(파일을 빼내도 암호문).
    # ORM 으로 읽을 땐 키(LAB_DB_ENC_KEY)로 투명하게 복호화돼 평문이 보인다.
    sensitive_memo = EncryptedTextField(blank=True, default="")
    # 복호화하면 드러나는 실습용 비밀번호 (실제 로그인에는 안 씀)
    lab_plaintext_password = EncryptedTextField(blank=True, default="")
    is_virtual = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
