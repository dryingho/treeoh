<h1 align="center">Treeoh</h1>

<p align="center">프로필과 대표 프로젝트, 블로그를 한곳에 모은 개인 포트폴리오</p>
<p align="center"><strong>Python · Django · SQLite</strong></p>

<p align="center">
  <a href="#사이트-둘러보기">사이트 둘러보기</a> ·
  <a href="#로컬에서-실행하기">로컬에서 실행하기</a> ·
  <a href="#콘텐츠-관리">콘텐츠 관리</a>
</p>

---

## 사이트 둘러보기

| 페이지 | 주요 기능 | 로컬 주소 |
| --- | --- | --- |
| **홈** | 프로필, 외부 링크, 대표 프로젝트, 최근 글을 한눈에 확인 | [`/`](http://127.0.0.1:8000/) |
| **소개** | 프로필과 자기소개 확인 | [`/about/`](http://127.0.0.1:8000/about/) |
| **블로그** | 글 읽기와 댓글 작성 | [`/board/`](http://127.0.0.1:8000/board/) |
| **운영자 화면** | 프로필, 외부 링크, 대표 프로젝트 편집 | [`/operator/`](http://127.0.0.1:8000/operator/) |

## 로컬에서 실행하기

프로젝트 폴더에서 PowerShell을 열고 가상 환경을 만든 뒤 의존성을 설치합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

마이그레이션으로 SQLite 데이터베이스를 준비한 뒤 개발 서버를 시작합니다.

```powershell
$env:LAB_MODE = "safe"
$env:DJANGO_DEBUG = "1"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

서버가 시작되면 브라우저에서 홈을 엽니다. [로컬에서 Treeoh 열기](http://127.0.0.1:8000/)

## 콘텐츠 관리

관리자 계정을 만들려면 개발 서버를 `Ctrl+C`로 중지하고 다음 명령을 실행합니다.

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

개발 서버를 다시 시작한 뒤 생성한 계정으로 로그인하면 콘텐츠를 관리할 수 있습니다. [Django 관리자 화면](http://127.0.0.1:8000/admin/)
