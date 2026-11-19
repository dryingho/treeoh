# systemd 로 실행 (선택)

Docker 없이 VM 에서 Django 를 서비스로 상시 실행하려면 사용한다. 수동 실행은
`scripts/run_web.sh` 로 충분하다. (업로드 파일 실행은 Django 가 담당하므로 별도
실행 서비스 유닛은 없다.)

## 준비
```bash
# 1) 코드 배치
sudo mkdir -p /opt/portfolio-incident-lab
sudo cp -r . /opt/portfolio-incident-lab/
cd /opt/portfolio-incident-lab
sudo cp .env.example .env            # 값 확인/수정 (POSTGRES_HOST=127.0.0.1)

# 2) 실행 사용자(비관리자) — 반드시 비(非)root
sudo useradd --system --shell /usr/sbin/nologin labuser || true

# 3) 초기 설치(venv/DB/seed) — labuser 권한으로
sudo -u labuser bash scripts/setup_vm.sh
```

## 설치/기동
```bash
sudo cp deploy/systemd/portfolio-lab-web.service /etc/systemd/system/
# 경로/User 를 환경에 맞게 수정했는지 확인
sudo systemctl daemon-reload
sudo systemctl enable --now portfolio-lab-web.service
sudo systemctl status portfolio-lab-web
```

## 수정 모드
`.env` 의 `DJANGO_SETTINGS_MODULE=config.settings.fixed` 로 바꾼 뒤 재시작한다.
이러면 업로드 파일 실행(`LAB_RUN_UPLOADS`)도 자동으로 꺼진다.

## 비(非)root 실행이 중요한 이유
업로드한 `.sh` 는 Django 프로세스 계정으로 실행된다. 반드시 `labuser` 같은 비관리자
계정으로 띄워, 실행 계정이 제한되고 그 계정이 증거(`whoami`)로 남도록 한다.

## DB 외부 미공개 확인
PostgreSQL 기본 설치는 `listen_addresses='localhost'` 이므로 호스트/외부에서 5432 로
직접 접속되지 않는다. `ss -lntp | grep 5432` 로 127.0.0.1 바인딩만 있는지 확인한다.
