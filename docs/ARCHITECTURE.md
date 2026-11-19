# 구성 요소와 공격 전제 조건 (ARCHITECTURE)

> 이 문서는 "구현 전 짧은 정리"의 확장판이다. 각 취약점의 **실제 동작 지점**,
> **전제 조건**, **모의(simulation) 처리한 부분**을 분명히 구분한다.

## 1. 서비스 구성 (로컬 VM)

```
                   ┌──────────────────────────────────────────────┐
 호스트 브라우저   │  VM (네이티브 프로세스, Docker 미사용)       │
   :8000  ───────►│  Django runserver                            │
                   │   ├─ 포트폴리오/게시판/운영자 패널            │
                   │   ├─ /uploads/run/<파일> → 업로드 파일 직접 실행│
                   │   └─► shared/uploads (avatars/, _evidence/)  │
                   │          └──► PostgreSQL(localhost only)      │
                   └──────────────────────────────────────────────┘
```

- **Django (`:8000`, `scripts/run_web.sh`)**: 포트폴리오/게시판/운영자 패널에 더해,
  업로드한 `.sh/.cgi` 를 `/uploads/run/<파일>` 에서 **직접 실행**한다(취약 모드만).
  별도 실행 서버는 없다. Django 를 **비(非)root** 로 실행해 실행 계정을 증거로 남긴다.
- **PostgreSQL**: `listen_addresses=localhost` → **호스트/외부에서 직접 접속 불가**.
- 외부 CDN/외부 수집 서버에 의존하지 않는다. 정적 파일/CSS 전부 로컬. **PHP·Docker 미사용.**

## 2. Django 앱 (책임 분리)

| 앱 | 책임 | 관련 취약점 |
|---|---|---|
| `accounts` | 운영자 프로필(소개/사진) | 업로드 저장 대상 |
| `portfolio` | 소개/프로젝트/메인/사이트 링크 | 사이트 변조 대상(`SiteLink`) |
| `board` | 게시글/댓글 | **저장형 XSS 발생 지점**(댓글 출력) |
| `operator_panel` | 운영자 로그인/수정/감사 로그 | 권한 악용 대상 엔드포인트 |
| `uploads` | 프로필 사진 업로드 | **파일 업로드 진입점** |
| `demo_records` | 가상 고객 데이터 | 평문 저장/유출 범위 |
| `lab` | seed/reset/status, 모의 수집기 | 초기화·증거·상태 |

## 3. 설정 분리 (취약은 명시적 opt-in)

- `config/settings/base.py` — 공통. **안전한 기본값**. 단독 실행 가능.
- `config/settings/vulnerable.py` — 취약. `DJANGO_SETTINGS_MODULE` 로 **명시 선택해야** 활성화.
- `config/settings/fixed.py` — 수정 완화책 적용.

런타임 분기는 `LAB_*` 플래그로 이뤄진다(`/lab/status/` 에서 현재 값 확인).

## 4. 공격 전제 조건 · 모의 처리 (핵심)

### (A) 저장형 XSS — 발생 지점은 "출력 경로"
- 댓글은 입력을 **가공 없이 저장**한다. 취약 여부는 출력에서 갈린다.
  - `LAB_COMMENTS_RENDER_SAFE=True`(vulnerable) → 템플릿이 `{{ body|safe }}` → **실행**.
  - `False`(base/fixed) → Django **자동 이스케이프** → 코드가 텍스트로 표시(안전).
- **HttpOnly 세션 쿠키의 영향**: 기본 Django 는 `SESSION_COOKIE_HTTPONLY=True` 라서
  `document.cookie` 로 `sessionid` 를 **읽을 수 없다**. 따라서:
  - **시나리오 A (권한 악용/강제 요청)**: 피해 운영자의 브라우저가 쿠키를 자동
    첨부하므로 **HttpOnly 여도 가능**. CSRF 토큰은 same-origin 스크립트가
    `csrftoken` 쿠키에서 읽어 헤더로 넣는다(`CSRF_COOKIE_HTTPONLY=False` 기본값)
    → CSRF 보호만으로 same-origin XSS 를 막지 못함.
  - **시나리오 B (세션 탈취/계정 이전)**: `document.cookie` 로 `sessionid` 를 읽어야
    하므로 **추가 취약 설정 `SESSION_COOKIE_HTTPONLY=False` 가 필요**하다. 이 설정은
    `vulnerable.py` 에만 있고 그 이유를 주석에 명시했다. 설정이 없으면 B 는 재현되지
    않으며 A 만 가능하다.
- **모의 처리**: 공격자의 "쿠키 수집 서버"는 외부가 아니라 **VM 내부 로컬 엔드포인트**
  `/lab/collector/` 로 모의한다. 수집 결과는 DB(`CollectorHit`)와
  `lab_collector/stolen_cookies.log` 에 남는다.
- **피해자/공격자 분리**: 서로 다른 테스트 브라우저 컨텍스트(일반 창 vs 시크릿 창/다른
  프로필)로 재현한다. 실제 비밀번호/실제 브라우저 프로필을 쓰지 않는다.

### (B) 프로필 사진 업로드 → 서버 측 실행
- 업로드 자체로는 저장만 된다. 실행은 **Django 의 실행 엔드포인트** `/uploads/run/<파일>` 에
  **접근할 때** 일어난다(기본 Django 동작이 아니라, 이 실습을 위해 일부러 만든 취약 뷰).
- **동작**: `uploads/views.py` 의 `run_file` 이 `avatars/` 폴더의 `.sh/.cgi` 를 `subprocess`
  (`bash`)로 실행하고 출력을 돌려준다. 실행은 **취약 모드(`LAB_RUN_UPLOADS=True`)에서만**.
- **URL 연결**: 업로드 저장 시 `served_url = http://localhost:8000/uploads/run/<파일>` 기록.
- **실행 권한/격리**: Django 프로세스 계정으로 실행된다 → **Django 를 비(非)root 로 실행**해야
  실행 계정이 제한된다. 실행 스크립트에는 **최소 권한 DB 계정**만 환경변수로 전달한다.
  경로 이탈 방지(`avatars/` 하위·파일명만)로 임의 파일 실행을 막는다.
- **검증 방식**: 리버스 셸 불필요. `whoami`·`id`·`hostname` 와 `_evidence/pwned_*.txt`
  증거 파일로 확인. 수정 모드(`LAB_RUN_UPLOADS=False`)에서는 실행 대신 평문 소스만 반환된다.
- **단계 분리**: ① 파일 저장(`UploadRecord`, 디스크) ② 파일 접근(`_evidence/exec_access.log`)
  ③ 서버 측 실행(`_evidence/pwned_*.txt`) — 각각 별도 아티팩트.

### (C) 사이트 변조와 리다이렉트
- 변조는 **사이트 링크 설정(`SiteLink`) 변경**으로 일어난다. 변경 값/시각/주체를
  `AuditLog` 에 기록한다.
- **기본 시나리오는 "클릭 시 이동"**(클릭형). 메인 페이지가 자동으로 리다이렉트되지
  않으므로 조사자는 사이트를 계속 확인할 수 있다. 페이지 접속 즉시 이동(HTTP 3xx /
  meta refresh / JS)은 구현하지 않는다(개념만 FIX 문서에서 비교).
- 업로드만으로 리다이렉트가 자동 발생하지 않는다. 변조는 권한 악용(시나리오 A)의 결과다.

### (D) Git 이력의 자격 증명 노출
- `scripts/create_lab_git_history.sh` 가 **1차 커밋(하드코딩) → 2차 커밋(환경 변수)** 의
  이력을 만든다. 과거 커밋에 옛 값이 남는다.
- 과거 값은 **현재 실습 DB 에서도 유효**(교체 전)하여, 파일에서 지우는 것과 실제
  교체(rotate)의 차이를 보인다(`scripts/rotate_leak_credential.sql`).
- **확보 경로(기본)**: 서버의 실습 프로젝트 디렉터리에 `.git` 이 남아 있는 경우.
  외부 GitHub 에 비밀을 게시하지 않는다.

### (E) DB 유출 범위
- Django 로그인 계정(`auth_user`)은 **기본 해시(PBKDF2)** 유지.
- `DemoCustomer` 는 가상 이름/`example.test` 이메일/가상 연락처/민감 메모/**실습용 평문
  비밀번호**(인증 미사용)를 가진다.
- 유출 계정 `app_legacy` 는 **`demo_records_democustomer` 만 SELECT** 가능. `auth_user`
  등은 권한이 없어 **거부**된다. 즉 평문 저장 사실만으로 "DB 전체 유출"로 결론내지 않는다.
- `scripts/leak_demo.py` 가 범위 내 조회 성공/범위 밖 거부/행 수/샘플을 증거 파일로 남긴다.

## 5. 모의(simulation) 처리 요약

| 항목 | 실제 | 모의 |
|---|---|---|
| 쿠키 수집 서버 | 전송은 실제 HTTP 요청 | 수집 '서버'는 로컬 `/lab/collector/` |
| 서버 측 실행 | `subprocess` 실제 실행 | 외부 연결/리버스 셸 없음, 증거는 로컬 파일 |
| 자격 증명 | 실습용 가짜 값(.env) | 실제 서비스/계정 아님 |
| 고객 데이터 | DB 에 실제 저장 | 전부 가상(`example.test`) |
| 조롱 게시글 | DB 에 실제 게시 | 가상 시나리오 단서, 실제 인물 주장 아님 |
