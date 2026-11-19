-- 최소 권한 DB 계정(app_legacy) 권한 설정 (수동 실행용 참고).
-- web_entrypoint.sh 가 동일 내용을 자동 수행한다.
-- 사용: PGPASSWORD=<lab_admin_pw> psql -h <host> -U lab_admin -d portfolio_lab -f grant_least_privilege.sql
--       (환경변수 치환이 없으므로 아래 역할명/테이블명을 직접 확인)

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_legacy;
GRANT CONNECT ON DATABASE portfolio_lab TO app_legacy;
GRANT USAGE ON SCHEMA public TO app_legacy;

-- 유출 범위: demo_records 테이블만 SELECT 허용.
GRANT SELECT ON demo_records_democustomer TO app_legacy;

-- 아래는 '일부러' 부여하지 않는다(유출 범위 밖임을 증명):
--   auth_user, operator_panel_auditlog, board_comment 등.
