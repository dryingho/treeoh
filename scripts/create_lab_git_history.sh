#!/usr/bin/env bash
# 실습용 Git 이력 생성 스크립트.
#
# 목적(요구사항 6):
#   - 1차 커밋: 실습 DB 계정 정보가 '하드코딩'된 설정 파일 포함.
#   - 2차 커밋: 환경 변수 방식으로 변경(작업 트리에서 값 제거).
#   - 과거 커밋에는 이전 값이 그대로 남는다 → 파일에서 지우는 것과
#     실제로 교체(rotate)하는 것의 차이를 보인다.
#
# 공격자 확보 경로(기본 시나리오):
#   - 서버의 실습 프로젝트 디렉터리에 .git 이력이 남아 있는 경우.
#   - 외부 GitHub 에 비밀 정보를 게시하지 않는다.
#
# 사용:
#   bash scripts/create_lab_git_history.sh [대상_디렉터리]
#   (기본 대상: ./git_exposure_demo)
set -euo pipefail

TARGET="${1:-$(pwd)/git_exposure_demo}"
LEAK_USER="${LAB_LEAK_DB_USER:-app_legacy}"
LEAK_PW="${LAB_LEAK_DB_PASSWORD:-legacy_pw_exposed_in_git_2019}"
DB_NAME="${POSTGRES_DB:-portfolio_lab}"

echo "[git-history] 대상: $TARGET"
rm -rf "$TARGET"
mkdir -p "$TARGET/deploy"
cd "$TARGET"

git init -q
git config user.email "legacy-dev@example.test"
git config user.name "legacy-dev"

# ── 1차 커밋: 하드코딩된 자격 증명 ─────────────────────────────
cat > deploy/db_config.py <<EOF
# deploy/db_config.py  (2019 레거시 설정)
# [주의] 실습용 하드코딩 자격 증명. 과거 커밋에 노출되는 값이다.
DB_HOST = "db"
DB_NAME = "${DB_NAME}"
DB_USER = "${LEAK_USER}"
DB_PASSWORD = "${LEAK_PW}"   # TODO: 환경 변수로 이동 필요
EOF
git add -A
GIT_AUTHOR_DATE="2019-03-11T10:00:00" GIT_COMMITTER_DATE="2019-03-11T10:00:00" \
  git commit -q -m "deploy: 초기 DB 설정 추가"

# ── 2차 커밋: 환경 변수 방식으로 변경 ─────────────────────────
cat > deploy/db_config.py <<'EOF'
# deploy/db_config.py  (환경 변수 방식으로 변경)
import os
DB_HOST = os.environ["POSTGRES_HOST"]
DB_NAME = os.environ["POSTGRES_DB"]
DB_USER = os.environ["LAB_LEAK_DB_USER"]
DB_PASSWORD = os.environ["LAB_LEAK_DB_PASSWORD"]  # 값은 .env 에서 주입
EOF
git add -A
GIT_AUTHOR_DATE="2021-07-02T09:30:00" GIT_COMMITTER_DATE="2021-07-02T09:30:00" \
  git commit -q -m "deploy: DB 자격 증명을 환경 변수로 이동"

echo "[git-history] 완료. 과거 노출 값 확인:"
echo "    git -C \"$TARGET\" log --oneline"
echo "    git -C \"$TARGET\" log -p -- deploy/db_config.py | grep -n DB_PASSWORD"
echo
echo "핵심: 2차 커밋이 '현재 파일'에서는 값을 지웠지만, 1차 커밋에는 여전히"
echo "      DB_PASSWORD 값이 남아 있다. 이 값이 현재 실습 DB 에서 그대로"
echo "      유효한지(교체 전) 는 scripts/leak_demo.py 로 검증한다."
