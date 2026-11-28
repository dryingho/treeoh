from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _fernet():
    key = settings.LAB_DB_ENC_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


class EncryptedTextField(models.TextField):
    """저장할 때 Fernet 로 암호화하고 조회할 때 복호화하는 TextField.

    DB 파일(db.sqlite3)에는 '암호문'만 남는다. 평문을 복원하려면 키(LAB_DB_ENC_KEY)가
    있어야 한다. 그래서 RCE 로 db.sqlite3 를 통째로 빼내도(§leak) 이 필드만은 암호문이고,
    과거 Git 커밋에 올라간 키까지 찾아야 복호화된다(= Git 이력 유출 시나리오).

    Fernet 은 매 저장마다 다른 암호문을 만든다(비결정적). 따라서 이 필드 값으로는
    filter/get 질의를 하지 않는다(이 랩에선 email 등 다른 필드로만 조회한다).
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return value
        return _fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            # 평문(미암호화) 이거나 다른 키로 암호화된 값 → 그대로 돌려준다.
            return value
