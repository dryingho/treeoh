# 수정 모드 (FIX_MODE)

> `DJANGO_SETTINGS_MODULE=config.settings.fixed` 로 실행하여 (업로드 실행도 자동으로 꺼짐),
> 같은 시연을 반복했을 때 **각 공격 단계가 어디서 차단되는지** 검증한다.

## 완화책 매핑

| 공격 단계 | 완화책 | 어디서 차단 | 설정/코드 |
|---|---|---|---|
| 저장형 XSS | 댓글 자동 이스케이프 | **출력** 시 `{{ body }}`(이스케이프) | `LAB_COMMENTS_RENDER_SAFE=False` |
| 세션 탈취 | 세션 쿠키 HttpOnly | `document.cookie` 접근 불가 | `SESSION_COOKIE_HTTPONLY=True` |
| 강제 요청 | SameSite 강화(+토큰) | cross-site 자동 전송 억제 | `SESSION_COOKIE_SAMESITE="Strict"` |
| 업로드 | 이미지 검증 + 재인코딩 | **저장** 전 거부/정화 | `LAB_UPLOAD_VALIDATE_IMAGE=True` |
| 서버 실행 | 업로드 파일 실행 차단 | Django 가 실행 거부(소스만) | `LAB_RUN_UPLOADS=False` |
| Git 자격 증명 | **교체(rotate)** | 과거 값 무효화 | `scripts/rotate_leak_credential.sql` |
| DB 유출 | 최소 권한 계정 | 범위 밖 테이블 거부 | `grant_least_privilege.sql` |

## 단계별 "어디서 막히나" (반복 시연)

1. **댓글 XSS**: 같은 payload 를 등록해도 출력이 이스케이프되어 `<script>` 가 **텍스트로**
   표시된다. 운영자가 열람해도 실행되지 않는다. → 1단계에서 차단.
2. **세션 탈취(B)**: `document.cookie` 에 `sessionid` 가 없어 수집기에 세션이 들어오지
   않는다(`CollectorHit.has_sessionid=False`). → 트리거돼도 탈취 실패.
3. **강제 요청(A)**: XSS 자체가 실행되지 않으므로 링크 변조 POST 가 발생하지 않는다.
4. **업로드**: `webshell.sh` 는 확장자 화이트리스트에서 거부되고, 이미지라도 Pillow
   재인코딩으로 숨은 바이트가 제거된다. → 저장 단계에서 차단.
5. **서버 실행**: 설령 파일이 있어도 `LAB_RUN_UPLOADS=False` 면 `/uploads/run/` 이
   실행하지 않고 **평문 소스**만 반환한다. `pwned_*.txt` 가 생성되지 않는다.
6. **Git 자격 증명**: `rotate_leak_credential.sql` 적용 후 과거 비밀번호로 접속하면
   `leak_demo.py` 가 **접속 실패**를 보고한다(= 교체 완료). 파일에서 지우기만 한 상태와
   대비된다.
7. **DB 유출 범위**: 최소 권한이 유지되므로 `auth_user` 는 여전히 거부. 평문 필드가 있어도
   범위가 좁음을 재확인.

## 비밀번호 해시 vs 복원 필요 개인정보 (요구사항 9)

- **Django 로그인 비밀번호(auth_user)**: 단방향 **해시(PBKDF2)** 로 저장한다. 원문 복원이
  **필요 없다**(검증은 재해싱 비교). 유출돼도 즉시 평문화되지 않는다.
- **개인정보(이름/연락처/메모 등)**: 서비스가 **원문을 다시 보여줘야** 하므로 해시로
  대체할 수 없다. 보호는 **접근 통제 + 최소 권한 + (필요 시) 복호 가능한 암호화 +
  감사**로 접근해야 한다. `DemoCustomer.lab_plaintext_password` 는 "복원이 필요 없는 값을
  평문으로 둔" 안티패턴을 보이기 위한 필드다(실제라면 해시 대상).
- 요점: "해시로 끝"이 아니라, **복원이 필요한 데이터는 다른 통제**가 필요하다.

## 실행 방법

```bash
# .env 에서 DJANGO_SETTINGS_MODULE=config.settings.fixed 로 전환 후 web 재기동
bash scripts/run_web.sh
# fixed 모드면 업로드 파일 실행(LAB_RUN_UPLOADS)이 자동으로 꺼진다 (별도 설정 불필요)
bash scripts/run_web.sh

# 자격 증명 교체 적용
source .venv/bin/activate
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" -f scripts/rotate_leak_credential.sql

# 반복 시연으로 차단 지점 확인 (DEMO.md 와 동일 절차)
```
