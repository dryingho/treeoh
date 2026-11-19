#!/usr/bin/env python
"""Django 관리 유틸리티.

기본 설정은 config.settings.base (안전) 이다.
취약 실습을 하려면 환경변수로 명시 선택한다:
    DJANGO_SETTINGS_MODULE=config.settings.vulnerable
수정 모드:
    DJANGO_SETTINGS_MODULE=config.settings.fixed
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # dotenv 미설치 시에도 동작
    pass


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django 를 import 할 수 없습니다. 가상환경 활성화 및 "
            "requirements.txt 설치를 확인하세요."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
