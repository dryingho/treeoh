# 실습 계정 (LAB ACCOUNTS)

> 이 파일은 **교육용 가상 환경**의 로그인 계정을 정리한 참고 문서다.
> 실제 서비스/인물과 무관하며, 운영 환경에 그대로 쓰면 안 된다.
> (이전에는 로그인 화면에 계정이 노출돼 있었으나, 이 파일로 분리했다.)

## 운영자 웹 로그인 (`/operator/login/`)

| 항목 | 값 |
|---|---|
| 아이디 | `operator` |
| 비밀번호 | `operator123!` |
| 이메일 | `operator@example.test` (가상) |
| 권한 | `is_staff=True` |

- 생성 위치: `lab/management/commands/seed_lab.py` 의 `OPERATOR_ID` / `OPERATOR_PW` 상수.
- `python manage.py seed_lab` 실행 시 자동 생성된다. 비밀번호를 바꾸려면 위 상수를 수정하고
  `reset_lab` → `seed_lab` 을 다시 돌리거나, Django 에서 직접 변경한다.

## 참고: 다른 "계정" 들 (로그인용 아님)

- **`demo_records` 의 가상 고객**: `DemoCustomer.lab_plaintext_password` 는 '평문 저장 위험'
  시연용 필드이며 **인증에 쓰이지 않는다**. 전부 가상 데이터(`example.test`).
- **DB 유출용 최소 권한 계정** `app_legacy`: Git 이력 노출 시나리오용. 값은 `.env`
  (`LAB_LEAK_DB_USER` / `LAB_LEAK_DB_PASSWORD`) 와 `scripts/create_lab_git_history.sh` 참고.

> 모든 비밀번호/계정은 실습 전용이다. 실제 자격 증명을 여기에 적지 않는다.
