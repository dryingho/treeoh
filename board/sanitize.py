"""댓글 본문 HTML 새니타이저 (저장형 XSS 방어 - 수정 모드).

학습 목표:
  - Django 자동 이스케이프(프레임워크 기능)에 '맡기는' 대신, 방어 로직을
    코드로 직접 구현해 '무엇을 어떻게 걸러내는지' 보이게 한다.
  - 정규식으로 <script> 를 지우는 '블랙리스트'는 쉽게 우회된다.
    그래서 여기서는 HTML 을 '파싱'한 뒤 '허용목록(allowlist)'에 맞춰
    다시 조립한다. (파서 기반 + 허용목록 = 올바른 방식)

동작 요약:
  - 허용 태그(굵게/링크 등)는 그대로 통과시키되,
  - 허용 속성만 남기고(이벤트 핸들러 on* 전부 제거),
  - 링크(href)는 안전한 스킴(http/https/mailto)만 허용(javascript: 차단),
  - 허용되지 않은 태그(<script> 등)는 '보이는 텍스트'로 이스케이프한다.
"""

from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

# 허용할 태그 -> 그 태그에서 허용할 속성 집합
ALLOWED_TAGS = {
    "b": set(), "strong": set(), "i": set(), "em": set(), "u": set(),
    "s": set(), "br": set(), "p": set(), "ul": set(), "ol": set(),
    "li": set(), "code": set(), "pre": set(), "blockquote": set(),
    "a": {"href"},
}
VOID_TAGS = {"br"}                              # 닫는 태그가 없는 태그
SAFE_URL_SCHEMES = {"http", "https", "mailto"}  # 링크에 허용할 스킴


def _safe_href(value):
    """href 값이 안전하면 그대로, 위험하면 None 을 돌려준다.
    javascript:, data:, vbscript: 같은 스킴을 차단한다.
    (상대 경로/프래그먼트처럼 스킴이 없는 경우는 허용한다.)"""
    value = (value or "").strip()
    try:
        scheme = urlparse(value).scheme.lower()
    except ValueError:
        return None
    if scheme == "" or scheme in SAFE_URL_SCHEMES:
        return value
    return None


class _CommentSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)  # &lt; 같은 엔티티를 먼저 디코드
        self.out = []

    # 여는 태그: <b>, <a href=...>
    def handle_starttag(self, tag, attrs):
        self._emit_open(tag, attrs)

    # 자가 닫힘 태그: <br/>
    def handle_startendtag(self, tag, attrs):
        self._emit_open(tag, attrs)

    # 닫는 태그: </b>
    def handle_endtag(self, tag):
        if tag in ALLOWED_TAGS and tag not in VOID_TAGS:
            self.out.append("</%s>" % tag)
        elif tag not in ALLOWED_TAGS:
            # 허용되지 않은 태그의 닫는 태그는 '텍스트'로 보이게 이스케이프
            self.out.append(escape("</%s>" % tag))

    # 텍스트: 항상 이스케이프해서 출력(여기서 XSS 가 끊긴다)
    def handle_data(self, data):
        self.out.append(escape(data))

    # 주석 <!-- --> 은 제거
    def handle_comment(self, data):
        pass

    def _emit_open(self, tag, attrs):
        if tag not in ALLOWED_TAGS:
            # 허용되지 않은 태그는 지우지 않고 '보이는 텍스트'로 남겨
            # 무엇이 걸러졌는지 학습자가 바로 확인할 수 있게 한다.
            self.out.append(escape(self.get_starttag_text() or ""))
            return

        kept = []
        for name, value in attrs:
            name = (name or "").lower()
            if name.startswith("on"):                 # onclick, onerror 등 전부 제거
                continue
            if name not in ALLOWED_TAGS[tag]:          # 허용 속성만 남김
                continue
            if name == "href":
                safe = _safe_href(value)
                if safe is None:                       # 위험 스킴 링크는 버림
                    continue
                value = safe
            kept.append(' %s="%s"' % (name, escape(value or "", quote=True)))

        extra = ' rel="nofollow noopener"' if tag == "a" else ""
        self.out.append("<%s%s%s>" % (tag, "".join(kept), extra))

    def result(self):
        return "".join(self.out)


def sanitize_comment_html(raw):
    """원본 댓글 문자열을 허용목록 기준으로 정화한 안전한 HTML 로 돌려준다."""
    parser = _CommentSanitizer()
    parser.feed(raw or "")
    parser.close()
    return parser.result()
