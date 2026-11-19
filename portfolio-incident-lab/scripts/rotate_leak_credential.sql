-- [수정 모드 - 요구사항 6/9] 유출된 DB 자격 증명을 '실제로 교체'한다.
-- 파일에서 값을 지우는 것(1차 대응)만으로는 과거 커밋의 값이 여전히 유효하다.
-- 비밀번호를 교체해야 과거 값이 무효화된다.
--
-- 사용: PGPASSWORD=<lab_admin_pw> psql -h <host> -U lab_admin -d portfolio_lab -f rotate_leak_credential.sql

ALTER ROLE app_legacy PASSWORD 'rotated_pw_after_incident';

-- 교체 후 검증: 과거(노출) 비밀번호로 로그인 시도 → 실패해야 정상.
--   PGPASSWORD=legacy_pw_exposed_in_git_2019 psql -h <host> -U app_legacy -d portfolio_lab -c 'select 1;'
--   => FATAL: password authentication failed for user "app_legacy"
