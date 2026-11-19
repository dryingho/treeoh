#!/usr/bin/env bash
# 네이티브(Docker 미사용) 설치 스크립트.
# 수행: venv 생성 → 의존성 설치 → DB 역할/DB 생성 → migrate →
#       최소 권한 계정(app_legacy) 생성/권한 → seed_lab.
# 멱등적으로 동작한다. 전제: Python 3.12, PostgreSQL 16 설치됨.
#
# 사용:
#   cp .env.example .env     # 값 확인/수정
#   bash scripts/setup_vm.sh
set -euo pipefail

cd "$(dirname "$0")/.."
PROJ="$(pwd)"

# ── .env 로드 ────────────────────────────────────────────────
if [[ -f .env ]]; then
  set -a; source .env; set +a
else
  echo "[setup] .env 가 없습니다. 'cp .env.example .env' 후 다시 실행하세요." >&2
  exit 1
fi

: "${POSTGRES_DB:=portfolio_lab}"
: "${POSTGRES_USER:=lab_admin}"
: "${POSTGRES_PASSWORD:=lab_admin_pw_change_me}"
: "${POSTGRES_HOST:=127.0.0.1}"
: "${POSTGRES_PORT:=5432}"
: "${LAB_LEAK_DB_USER:=app_legacy}"
: "${LAB_LEAK_DB_PASSWORD:=legacy_pw_exposed_in_git_2019}"

# ── 1) venv + 의존성 ─────────────────────────────────────────
if [[ ! -d .venv ]]; then
  echo "[setup] venv 생성..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install -r requirements.txt

# ── 2) DB 역할/DB 생성 (postgres 슈퍼유저) ───────────────────
# 로컬 소켓으로 postgres 로 접속해 역할/DB 를 멱등 생성한다.
echo "[setup] DB 역할/DB 생성(postgres)..."
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
    CREATE ROLE ${POSTGRES_USER} LOGIN PASSWORD '${POSTGRES_PASSWORD}';
  ELSE
    ALTER ROLE ${POSTGRES_USER} PASSWORD '${POSTGRES_PASSWORD}';
  END IF;
  -- 최소 권한 계정도 여기서(슈퍼유저 권한으로) 만든다. lab_admin 은 역할 생성 권한이 없다.
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${LAB_LEAK_DB_USER}') THEN
    CREATE ROLE ${LAB_LEAK_DB_USER} LOGIN PASSWORD '${LAB_LEAK_DB_PASSWORD}';
  ELSE
    ALTER ROLE ${LAB_LEAK_DB_USER} PASSWORD '${LAB_LEAK_DB_PASSWORD}';
  END IF;
END \$\$;
SELECT 'CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}')\gexec
SQL

export PGPASSWORD="$POSTGRES_PASSWORD"
PSQL="psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -d ${POSTGRES_DB}"

# ── 3) 마이그레이션 ──────────────────────────────────────────
echo "[setup] migrate..."
python manage.py migrate --noinput

# ── 4) 최소 권한 계정 권한 설정 (역할은 2단계에서 생성됨) ─────
echo "[setup] 최소 권한 계정(${LAB_LEAK_DB_USER}) 권한 설정..."
$PSQL -v ON_ERROR_STOP=1 <<SQL
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ${LAB_LEAK_DB_USER};
GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${LAB_LEAK_DB_USER};
GRANT USAGE ON SCHEMA public TO ${LAB_LEAK_DB_USER};
-- 유출 범위: demo_records 테이블만 SELECT (auth_user 등은 미부여)
GRANT SELECT ON demo_records_democustomer TO ${LAB_LEAK_DB_USER};
SQL

# ── 5) seed ──────────────────────────────────────────────────
echo "[setup] seed_lab..."
python manage.py seed_lab

echo
echo "[setup] 완료. 아래 명령으로 서버를 실행하세요:"
echo "    bash scripts/run_web.sh       # Django  :8000 (업로드 파일 실행도 Django 가 담당)"
