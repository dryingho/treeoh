# 공격 시연 (DEMO)

> 공격 진행 순서(요구사항 8):
> 댓글 등록 → 운영자의 댓글 열람 → 운영자 권한 악용 → 프로필 업로드 경로 악용 →
> 서버 실행 확인 → Git 이력의 DB 정보 확인 → 가상 DB 데이터 조회.
>
> **전 과정을 건너뛰는 "공격 성공 버튼"은 없다.** 각 단계는 실제 동작과 증거로 확인한다.
> 피해 운영자/공격자는 **서로 다른 브라우저 컨텍스트**로 재현한다
> (예: 일반 창 = 피해 운영자, 시크릿 창 = 공격자).

전제: `scripts/setup_vm.sh` 로 설치가 끝나고 `run_web.sh` 가 떠 있는 vulnerable 모드
상태(`seed_lab` 적용됨). 업로드 파일 실행도 Django 가 담당한다. 시작 명령은 README 3절 참고.

---

## 단계 0. 상태 확인 (기준선)
- **수행 위치**: 호스트 브라우저 `http://localhost:8000/lab/status/`
- **기대 결과**: mode=vulnerable, 변조 링크=0, 업로드 실행 후보=0, 증거 파일=없음
- **확인 로그**: `python manage.py lab_status`

## 단계 1. 댓글 등록 (저장형 XSS 주입)
- **선행 조건**: vulnerable 모드(`LAB_COMMENTS_RENDER_SAFE=True`)
- **수행 위치(공격자 컨텍스트)**: 게시글 상세의 댓글 폼. 대상 게시글은 아무거나 가능.
- **수행 내용**:
  - 시나리오 A(권한 악용): `attack/xss_forced_action.txt` 의 `<script>` 를 댓글로 등록.
  - 시나리오 B(세션 탈취): `attack/xss_session_theft.txt` 의 `<script>` 를 댓글로 등록.
- **기대 결과**: 댓글이 저장됨(이 시점엔 아직 실행 안 됨 — 저장만).
- **확인 로그**: `board_comment` 행 증가, `/lab/status/` 의 "스크립트성 댓글" 증가.
- **실패 원인**: base/fixed 모드면 출력이 이스케이프되어 텍스트로만 보임(정상 방어).

## 단계 2. 운영자의 댓글 열람 (트리거)
- **선행 조건**: 단계 1 완료. 운영자가 해당 댓글을 **본다**.
- **수행 위치(피해 운영자 컨텍스트)**: 일반 창에서 `operator/operator123!` 로그인 후
  해당 게시글 상세를 연다.
- **기대 결과**:
  - A: 운영자 세션으로 `/operator/links/` 에 강제 POST → `resume` 링크가 웹쉘 주소로 변조.
  - B: `document.cookie` 가 `/lab/collector/` 로 전송.
- **확인 로그**:
  - A: `/operator/audit/` 에 `link_change`(actor=operator), `/lab/status/` 변조 링크=1.
  - B: `lab_collector/stolen_cookies.log` 또는 Django admin "수집기 수신(모의)".
- **실패 원인**: 운영자가 댓글을 열지 않으면 실행 안 됨(저장형 XSS 는 열람이 트리거).

## 단계 3. 운영자 권한 악용 (결과 확인)
- **선행 조건**: 단계 2-A 또는 B.
- **A(강제 요청)**: 메인 페이지 `resume` 링크에 "변조됨" 배지, `AuditLog` 에 전/후 값과 시각.
- **B(세션 탈취)**: 공격자 컨텍스트(시크릿 창)에서 수집된 `sessionid` 를 주입
  (`attack/xss_session_theft.txt` 하단 절차) → 로그인 없이 `/operator/` 접근.
- **확인 로그**: `AuditLog`(A), `CollectorHit.has_sessionid`(B).
- **실패 원인**: B 는 `SESSION_COOKIE_HTTPONLY=False` 가 없으면 `sessionid` 미포함 → 실패(정상).

## 단계 4. 프로필 업로드 경로 악용 (파일 저장)
- **선행 조건**: 운영자 권한(정상 로그인 또는 탈취 세션). vulnerable 업로드 설정.
- **수행 위치**: `/uploads/avatar/` 에서 `attack/webshell.sh` 를 업로드.
- **기대 결과**: 확장자/내용 검증 없이 저장. 경고 메시지에 실행 주소(/uploads/run/) 노출.
- **확인 로그**: `UploadRecord`(is_executable_candidate=True), 디스크
  `shared/uploads/avatars/webshell.sh`.
- **실패 원인**: fixed 모드면 확장자 화이트리스트/재인코딩으로 거부됨(정상 방어).

## 단계 5. 서버 실행 확인 (파일 접근 → 서버 측 실행)
- **선행 조건**: 단계 4 완료. (변조된 `resume` 링크 또는 직접 URL)
- **수행 위치**: 브라우저/`curl` 로 `http://localhost:8000/uploads/run/webshell.sh` 접근.
  - 기본 시나리오에서는 메인 페이지의 변조된 `resume` 링크를 **클릭**해 이동.
- **기대 결과**: Django 가 스크립트를 **실행**하고 출력 반환. `_evidence/pwned_*.txt` 생성.
- **확인 로그(증거)**:
  - 실행 계정: `whoami` = Django 실행 계정(비root 로 띄웠다면 그 계정)
  - 접근 기록: `shared/uploads/_evidence/exec_access.log` (GET/EXEC 라인)
  - 실행 증거: `shared/uploads/_evidence/pwned_*.txt`
  - `python manage.py lab_status` 의 "서버 실행 증거 파일" 목록
- **실패 원인**: 수정 모드(`LAB_RUN_UPLOADS=False`)면 실행되지 않고 평문 소스만 반환.

## 단계 6. Git 이력의 DB 정보 확인
- **선행 조건**: `bash scripts/create_lab_git_history.sh` 로 실습 저장소 생성(1회).
- **수행 위치**: 서버의 해당 디렉터리.
- **수행 내용**:
  ```bash
  git -C git_exposure_demo log --oneline
  git -C git_exposure_demo log -p -- deploy/db_config.py | grep -n DB_PASSWORD
  ```
- **기대 결과**: 2차 커밋에선 사라졌지만 1차 커밋에 `DB_PASSWORD` 가 남아 있음.
- **확인 로그**: `git log -p` 출력(=조사자가 복구한 '사실').
- **실패 원인**: 저장소 미생성 또는 `.git` 부재.

## 단계 7. 가상 DB 데이터 조회 (유출 범위)
- **선행 조건**: 단계 6 에서 복구한 자격 증명(app_legacy).
- **수행 위치**: 서버(또는 업로드한 `webshell.sh` 가 실행될 때 자동으로도 수행됨).
- **수행 내용**:
  ```bash
  python scripts/leak_demo.py --host 127.0.0.1 --dbname portfolio_lab \
    --user app_legacy --password legacy_pw_exposed_in_git_2019
  ```
  (또는 단계 5 의 `webshell.sh` 가 이미 범위 검증을 수행)
- **기대 결과**:
  - `demo_records_democustomer`: 조회 성공(행 수/샘플) — **유출 범위 내**
  - `auth_user`: **권한 거부** — 유출 범위 밖
- **확인 로그(증거)**: `shared/uploads/_evidence/leak_scope_*.txt`
- **실패 원인**: 자격 증명이 이미 교체(rotate)됐으면 접속 실패(수정 모드에서 정상).

---

### 단계별 산출물 요약

| 단계 | 산출 증거 |
|---|---|
| 1 댓글 | `board_comment` 행 |
| 2~3 권한 악용 | `AuditLog`(link_change) / `CollectorHit`(sessionid) |
| 4 업로드 | `UploadRecord`, `avatars/webshell.sh` |
| 5 실행 | `_evidence/exec_access.log`, `_evidence/pwned_*.txt`(whoami=Django 실행 계정) |
| 6 Git | `git log -p` 의 과거 `DB_PASSWORD` |
| 7 유출 | `_evidence/leak_scope_*.txt`(범위 내 성공/범위 밖 거부) |
