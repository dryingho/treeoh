# 사고 조사 (INVESTIGATION)

> 조사 순서(요구사항 8):
> 조롱 게시글 발견 → 변조된 링크 확인 → 업로드 파일과 접근 기록 조사 →
> 댓글과 운영자 활동 조사 → 과거 Git 커밋 확인 → DB 유출 범위 확인.
>
> **원칙**: 로그에 기록된 **사실**과 조사자의 **추정**을 반드시 구분한다.
> 각 절의 "사실"은 DB/파일에서 직접 확인되는 값, "추정"은 그로부터의 해석이다.

---

## 1. 조롱 게시글 발견 (출발점)
- **수행 위치**: `http://localhost:8000/board/`
- **사실**: 제목 "오주성 포트폴리오 사이트 대학생한테 다 털렸죠?ㅋㅋㅋㅋㅋ" 게시글 존재
  (`is_scenario_clue=True`, 작성자 표시 `unknown`).
- **추정**: 누군가 사고를 조롱/암시. **단, 이 게시글 자체는 가상 시나리오 단서이며
  실제 인물/행위를 주장하지 않는다.**
- **확인 로그**: `board_post` 행, 작성 시각.
- **다음 단서**: 사이트에 실제 변조가 있었는지 확인.

## 2. 변조된 링크 확인
- **수행 위치**: 메인 페이지 / `/operator/audit/` / `/lab/status/`
- **사실**:
  - `SiteLink.is_defaced=True`, `resume` 의 `url` 이 `http://localhost:8000/uploads/run/...` 로 변경.
  - `AuditLog`: `action=link_change`, `old_value`→`new_value`, `created_at`, `actor`.
- **추정**: 링크가 업로드 파일 실행 주소(/uploads/run/)로 바뀐 것으로 보아 업로드 경로와 연관.
- **확인 로그**: `AuditLog`(변경 전/후·시각·주체·IP).
- **주의(사실 vs 추정)**: `actor=operator` 는 "운영자 계정의 세션"에서 요청됐다는 **사실**
  이지, "운영자 본인이 직접 했다"는 **증명이 아니다**(세션 악용 가능성).

## 3. 업로드 파일과 접근 기록 조사
- **수행 위치**: 서버 `shared/uploads/`, Django admin `업로드 기록`
- **사실**:
  - `UploadRecord`: `webshell.sh`, `is_executable_candidate=True`, 업로더/시각.
  - 파일 존재: `shared/uploads/avatars/webshell.sh`.
  - 접근 기록: `shared/uploads/_evidence/exec_access.log` 의 `GET`/`EXEC` 라인.
  - 실행 증거: `shared/uploads/_evidence/pwned_*.txt` (`whoami`=Django 실행 계정, DB 범위 결과).
- **추정**: 업로드된 스크립트가 Django 실행 엔드포인트에서 실행되어 서버 측 코드 실행 발생.
- **확인 로그**: 위 3종(저장/접근/실행)이 **서로 다른 아티팩트**로 분리됨에 주목.
- **실패/한계**: `pwned_*.txt` 가 없으면 "저장"까지만 확인된 것. 실행 여부는 접근 로그와
  증거 파일로만 확정(추정 금지).

## 4. 댓글과 운영자 활동 조사
- **수행 위치**: Django admin `댓글`, `/operator/audit/`
- **사실**:
  - `Comment.looks_like_script=True` 인 댓글(스크립트성 본문)과 작성 IP/시각/UA.
  - `CollectorHit`(모의 수집기 수신): 수신 시각/`has_sessionid`.
  - `AuditLog`: 로그인/변경 이력.
- **추정**: 저장형 XSS 댓글 → 운영자 열람 시 트리거 → 링크 변조/쿠키 전송.
- **확인 로그**: 댓글 작성 시각과 `AuditLog`/`CollectorHit` 시각의 **선후 관계**.
- **주의**: `CollectorHit.has_sessionid=True` 면 세션 탈취 성립 가능. `False` 면 쿠키에
  `sessionid` 미포함 → (HttpOnly 등으로) 탈취 실패를 시사(사실), 그러나 강제 요청형
  악용은 별개로 가능(추정 시 혼동 주의).

## 5. 과거 Git 커밋 확인
- **수행 위치**: 서버의 실습 프로젝트 디렉터리(`.git` 잔존)
- **사실**:
  ```bash
  git -C git_exposure_demo log --oneline
  git -C git_exposure_demo log -p -- deploy/db_config.py
  ```
  1차 커밋에 `DB_USER`/`DB_PASSWORD` 하드코딩, 2차 커밋에서 env 전환.
- **추정**: 공격자가 `.git` 에서 과거 DB 자격 증명을 복구했을 가능성.
- **확인 로그**: `git log -p` 의 과거 값.
- **핵심**: 현재 파일에 값이 없다고 안전한 것이 아니다(교체 여부는 6에서 확인).

## 6. DB 유출 범위 확인
- **수행 위치**: 서버
  ```bash
  python scripts/leak_demo.py --user app_legacy \
    --password <git 에서 복구한 값>
  ```
- **사실(증거 `_evidence/leak_scope_*.txt`)**:
  - 접속 성공 여부(= 과거 값이 현재도 유효한지).
  - `demo_records_democustomer`: 행 수/샘플(범위 내).
  - `auth_user` 등: 권한 거부(범위 밖).
- **추정**: 유출 범위는 `app_legacy` 권한 테이블로 한정. 평문 저장 사실만으로 전체 DB
  유출로 단정하지 않는다.
- **확인 로그**: 조회된 테이블 목록 + 행 수 + 거부 메시지.

---

## 사실 vs 추정 체크리스트

| 관측(사실) | 바로 말할 수 없는 것(추정 주의) |
|---|---|
| `AuditLog.actor=operator` | "운영자 본인이 직접 변경했다" (세션 악용 가능) |
| 스크립트성 댓글 존재 | "반드시 실행됐다" (열람/출력 설정에 의존) |
| `UploadRecord` 저장됨 | "서버에서 실행됐다" (접근·증거 파일로만 확정) |
| 평문 비밀번호 존재 | "DB 전체가 유출됐다" (권한 범위로 한정) |
| `.git` 에 과거 값 | "현재도 유효하다" (교체 여부로 확정) |
