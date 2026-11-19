#!/usr/bin/env bash
# Django 개발 서버 실행 (Docker 미사용).
# 전제: scripts/setup_vm.sh 를 먼저 1회 수행(venv/DB/seed 준비).
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .env ]] && { set -a; source .env; set +a; }
# shellcheck disable=SC1091
source .venv/bin/activate

: "${DJANGO_SETTINGS_MODULE:=config.settings.vulnerable}"
export DJANGO_SETTINGS_MODULE
# 업로드는 프로젝트 내부 공유 디렉터리에 저장(실행 서비스와 공유)
export LAB_MEDIA_ROOT="$(pwd)/shared/uploads"

echo "[web] settings=${DJANGO_SETTINGS_MODULE}  media=${LAB_MEDIA_ROOT}"
exec python manage.py runserver 0.0.0.0:8000
