-- 네이티브 PostgreSQL 초기화 (Docker 미사용).
-- postgres 슈퍼유저로 실행한다:
--   sudo -u postgres psql -v admin_pw="'lab_admin_pw_change_me'" -f scripts/init_db_native.sql
-- (psql -v 치환을 쓰거나, 아래 값을 .env 와 맞춰 직접 수정)
--
-- 생성물: 관리/마이그레이션용 전체 권한 계정(lab_admin) + 실습 DB.
-- 최소 권한 계정(app_legacy)은 마이그레이션 이후 grant_least_privilege.sql 로 부여.

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lab_admin') THEN
    CREATE ROLE lab_admin LOGIN PASSWORD 'lab_admin_pw_change_me';
  END IF;
END $$;

SELECT 'CREATE DATABASE portfolio_lab OWNER lab_admin'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'portfolio_lab')\gexec

-- 보안 경계: 이 DB 는 호스트/외부에 포트를 공개하지 않는다.
-- postgresql.conf 의 listen_addresses 는 기본값('localhost')을 유지하고,
-- pg_hba.conf 는 local / 127.0.0.1 접속만 허용하도록 둔다(기본 설치 상태).
