# portfolio-incident-lab

로컬 VM 전용 **교육용 보안 실습 환경**. 한국어 포트폴리오 사이트에서 일어나는 사고
(댓글 저장형 XSS → 운영자 권한 악용 → 프로필 사진 업로드 → 서버 측 파일 실행 →
과거 Git 커밋의 DB 자격 증명 노출 → 평문 가상 데이터 유출)를 **실제 동작과 증거**로
재현하고, 같은 흐름을 **수정 모드**에서 어디서 차단되는지까지 검증한다.

> ⚠️ **의도적으로 취약하게 만든 교육용 환경**입니다. 실제 서비스/실제 사용자 정보가
> 없으며, 모든 데이터는 가상(`example.test`)입니다. **로컬 VM 안에서만** 실행하세요.
> 인터넷에 노출하지 마세요. 초기 데이터의 조롱 게시글은 **가상 시나리오 단서**이며
> 실제 인물/행위를 주장하지 않습니다.

> **Docker 를 사용하지 않습니다.** PostgreSQL + Python venv 기반으로 VM 에서 직접 실행합니다.

---

## 0. 버전 / 호환성

| 항목 | 버전 | 비고 |
|---|---|---|
| Python | **3.12** (권장) | Django 5.2 LTS 는 3.10–3.13 지원 |
| Django | **5.2.7 (LTS)** | `requirements.txt` 고정 |
| PostgreSQL | **16** (VM 네이티브 설치) | `listen_addresses=localhost` 유지 |
| psycopg | 3.2.x | `psycopg[binary]` |
| 실행 서비스 | 순수 Python 3.12 | **PHP·Docker 미사용** |

> 참고: 본 저장소를 만든 개발 호스트는 Python 3.14 였고, 거기서는
> `makemigrations`/`check`/`compileall` 정적 검증을 위해 최신 `psycopg` 휠을 설치했습니다.
> **VM 데모 기준은 Python 3.12** 입니다.

## 1. 공격/수정 전제 요약

- **저장형 XSS**: 댓글 **출력 경로**에서 발생(`|safe`). 저장은 가공하지 않음.
- **세션**: 기본 Django 는 `HttpOnly=True` 라 `document.cookie` 로 세션 미노출.
  - **권한 악용(강제 요청)**: HttpOnly 여도 가능(브라우저가 쿠키 자동 첨부).
  - **세션 탈취**: `SESSION_COOKIE_HTTPONLY=False`(취약 설정에만) 필요.
  - 수집 서버는 **로컬 모의**(`/lab/collector/`), 외부 전송 없음.
- **업로드 실행**: 업로드한 `.sh/.cgi` 를 **Django 가 `/uploads/run/<파일>` 에서 직접 실행**
  (취약 모드에서만). 증거 파일로 검증, 리버스 셸 없음. Django 를 비(非)root 로 실행할 것.
- **변조**: 사이트 링크 설정 변경(값/시각 기록). **클릭 시 이동**(자동 리다이렉트 아님).
- **Git 노출**: 1차 커밋 하드코딩 → 2차 env. 과거 값이 **현재도 유효**(교체 전).
- **DB 유출 범위**: 최소 권한 계정은 `demo_records` 만 조회. `auth_user` 는 거부.

자세한 내용: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 2. 디렉터리 구조

```
portfolio-incident-lab/
├─ config/settings/{base,vulnerable,fixed}.py   # 설정 분리(취약은 opt-in)
├─ accounts/ portfolio/ board/ operator_panel/  # Django 앱(책임 분리)
│  uploads/ demo_records/ lab/
├─ templates/ static/                           # Django Templates + 단순 CSS
│  # 업로드 파일 실행은 Django(uploads 앱 /uploads/run/)가 담당 — 별도 실행 서버 없음
├─ scripts/
│  ├─ setup_vm.sh                  # venv→DB→migrate→최소권한→seed (네이티브 설치)
│  ├─ run_web.sh                   # Django 실행(:8000)
│  ├─ init_db_native.sql           # DB 역할/DB 생성(수동 참고)
│  ├─ grant_least_privilege.sql    # 최소 권한 부여(수동 참고)
│  ├─ rotate_leak_credential.sql   # 자격 증명 교체(수정)
│  ├─ create_lab_git_history.sh    # Git 이력(자격 증명 노출) 생성
│  └─ leak_demo.py                 # DB 유출 범위 검증
├─ deploy/systemd/                  # (선택) systemd 유닛 + 비관리자 실행 안내
├─ attack/                          # 실습 payload(수동, 자동 성공 버튼 아님)
│  ├─ webshell.sh  xss_forced_action.txt  xss_session_theft.txt
├─ docs/{ARCHITECTURE,DEMO,INVESTIGATION,FIX_MODE}.md
├─ shared/uploads/{avatars,_evidence}/          # Django↔실행 서비스 공유
├─ requirements.txt  .env.example
```

## 3. 빈 VM에서 설치·시연 (순서대로, Docker 없음)

> 전제: Ubuntu 등 리눅스 VM. **일반(비root) 사용자**로 로그인. 아래 패키지 설치.

```bash
# 0) 시스템 패키지
sudo apt update
sudo apt install -y python3.12 python3.12-venv postgresql-16 postgresql-client git
# (배포판에 3.12 패키지가 없으면 deadsnakes PPA 등으로 설치)

# 1) 환경 변수
cp .env.example .env            # 값은 전부 실습용 가짜. 필요 시 비밀번호만 변경
#   POSTGRES_HOST=127.0.0.1, DJANGO_SETTINGS_MODULE=config.settings.vulnerable

# 2) 설치 (venv/의존성/DB/역할/마이그레이션/최소권한/seed 를 한 번에)
bash scripts/setup_vm.sh
#   내부에서 'sudo -u postgres psql' 로 DB 역할/DB 를 생성하므로 sudo 권한이 필요

# 3) 서버 실행 (업로드 파일 실행도 Django 가 담당 — 별도 실행 서버 없음)
bash scripts/run_web.sh          # Django   http://localhost:8000
#   (Django 를 root 로 실행하지 말 것 — 실행 계정이 그대로 증거에 남는다)

# 4) 상태 확인(기준선)
curl -s 'http://localhost:8000/lab/status/?format=json' | python3 -m json.tool
#   접속: 포트폴리오 http://localhost:8000/ , 운영자 /operator/ (operator / operator123!)

# 5) Git 이력(자격 증명 노출) 생성 — 1회
bash scripts/create_lab_git_history.sh "$(pwd)/git_exposure_demo"

# 6) 공격 시연 — docs/DEMO.md 순서대로 (수동)
#    댓글 등록 → 운영자 열람 → 권한 악용 → 업로드 → 실행 확인 → Git 확인 → DB 조회
# 7) 사고 조사 — docs/INVESTIGATION.md 순서대로

# 8) 초기화 / 상태 (venv 활성화 상태에서)
source .venv/bin/activate
python manage.py lab_status
python manage.py reset_lab --seed
```

> 상시 서비스로 올리려면 `deploy/systemd/` 의 유닛과 안내를 참고.

### 수정 모드로 재검증

```bash
# .env 수정: DJANGO_SETTINGS_MODULE=config.settings.fixed
# -> 이러면 업로드 파일 실행(LAB_RUN_UPLOADS)이 꺼져서 실행 대신 소스만 보인다
bash scripts/run_web.sh

# 자격 증명 교체(과거 노출 값 무효화)
source .venv/bin/activate
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" -f scripts/rotate_leak_credential.sql

# 같은 시연 반복 → docs/FIX_MODE.md 의 "어디서 막히나" 확인
```

## 4. 관리 명령 / 상태

```bash
source .venv/bin/activate
python manage.py seed_lab      # 실습 초기 데이터(멱등)
python manage.py reset_lab     # 실습 데이터/업로드 초기화 (이 프로젝트 소유분만)
python manage.py reset_lab --seed
python manage.py lab_status    # 현재 모드/플래그/흔적 수치/증거 파일
```
웹 상태: `http://localhost:8000/lab/status/` (스킵 버튼 아님, 관측 수치만 표시)

## 5. 검증: 실제 실행한 것 vs 실행하지 못한 것

본 산출물은 **Windows 개발 호스트(PostgreSQL/리눅스 서비스 없음)** 에서 작성되었습니다.

### ✅ 실제로 실행·검증함 (이 저장소 작성 환경)
- `python manage.py makemigrations` → 7개 앱 마이그레이션 생성 완료(저장소 포함).
- `python manage.py check` (vulnerable / fixed 양쪽) → **0 issues**.
- `python -m compileall` (전체 앱 + `leak_demo.py` + `manage.py`) → **통과**.

### ⛔ 아직 실행하지 못함 (리눅스 VM 에서 수행 필요)
- `scripts/setup_vm.sh` 전체(로컬 PostgreSQL 연결·`migrate`·최소 권한 `GRANT`·`seed`).
- `run_web.sh` 런타임, 저장형 XSS 브라우저 트리거, 세션 쿠키 수집,
  업로드→**Django 의 서버 측 실행**(`/uploads/run/`, `pwned_*.txt`),
  `create_lab_git_history.sh`(이 호스트에 `git` 없음), `leak_demo.py` 의 실제 DB 조회.

> **코드/구성/마이그레이션/문서**는 정적 검증을 통과했고, **런타임 공격·조사 시연**은
> 위 "빈 VM 설치·시연" 절차대로 리눅스 VM 에서 수행하면 됩니다.

## 6. 안전 경계 (설계상 보장)
- PostgreSQL 은 `localhost` 만 바인딩(호스트/외부 미공개). `ss -lntp | grep 5432` 로 확인.
- 외부 CDN/수집 서버 미사용, 리버스 셸 없음.
- 업로드 파일 실행은 **취약 모드(LAB_RUN_UPLOADS)에서만**, `avatars/` 폴더의 `.sh/.cgi` 로 한정.
  Django 를 **비(非)root** 로 실행해 실행 계정을 증거로 남긴다. 수정 모드에선 실행이 꺼진다.
- 호스트 민감 파일/실제 자격 증명 미연결. 모든 자격 증명·개인정보는 실습용 가짜 값.
