from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import OperatorProfile
from board.models import Post
from demo_records.models import DemoCustomer
from portfolio.models import Project, SiteLink

User = get_user_model()

# 운영자 계정 (실습용 고정 값)
OPERATOR_ID = "operator"
OPERATOR_PW = "operator123!"

# 가상 고객: (이름, 이메일, 연락처, 메모, 평문 비밀번호)
CUSTOMERS = [
    ("김민준", "minjun.kim@example.test", "010-0000-0001", "VIP 등급(가상).", "pw-min-2019!"),
    ("이서연", "seoyeon.lee@example.test", "010-0000-0002", "뉴스레터 거부(가상).", "seoyeon#pw"),
    ("박도윤", "doyun.park@example.test", "010-0000-0003", "결제 보류(가상).", "doyun-1234"),
    ("최지우", "jiwoo.choi@example.test", "010-0000-0004", "내부 시연용 메모(가상).", "jiwoo!secret"),
    ("정하은", "haeun.jung@example.test", "010-0000-0005", "주소 변경 이력(가상).", "haeun-pass9"),
    ("강시우", "siwoo.kang@example.test", "010-0000-0006", "쿠폰 의심(가상).", "siwoo_pw!"),
    ("윤수아", "sua.yoon@example.test", "010-0000-0007", "테스트 계정(가상).", "sua-0007"),
    ("임지호", "jiho.lim@example.test", "010-0000-0008", "가상 데이터.", "jiho!pw2020"),
]

# 프로젝트: (제목, 요약, 설명, 기술)
PROJECTS = [
    ("실시간 대시보드", "실시간 모니터링", "지표를 실시간으로 보여주는 프로젝트(가상).", "React, Django"),
    ("추천 시스템 PoC", "추천 엔진", "행동 로그 기반 추천 PoC(가상).", "Python, PostgreSQL"),
    ("보안 실습 포털", "취약점 재현 환경", "이 사이트가 그 결과물입니다(가상).", "Django, PostgreSQL"),
]

# 사고 발견용 조롱 게시글 제목
MOCK_TITLE = "오주성 포트폴리오 사이트 대학생한테 다 털렸죠?ㅋㅋㅋㅋㅋ"


class Command(BaseCommand):
    help = "실습 초기 데이터를 만든다 (여러 번 실행해도 안전)"

    def handle(self, *args, **options):
        # 1) 운영자 계정
        operator, created = User.objects.get_or_create(
            username=OPERATOR_ID,
            defaults={"is_staff": True, "email": "operator@example.test"},
        )
        if created:
            operator.set_password(OPERATOR_PW)
            operator.save()

        profile, _ = OperatorProfile.objects.get_or_create(user=operator)
        if profile.bio == "":
            profile.display_name = "오주성(가상)"
            profile.bio = "백엔드/보안에 관심 많은 대학생 개발자입니다. (가상 프로필)"
            profile.save()

        # 2) 프로젝트
        order = 0
        for title, summary, desc, tech in PROJECTS:
            Project.objects.get_or_create(
                title=title,
                defaults={"summary": summary, "description": desc, "tech": tech, "order": order},
            )
            order += 1

        # 3) 메인 링크 (resume 가 변조 대상)
        links = [
            ("resume", "이력서/소개 보기", "/about/"),
            ("github", "GitHub", "https://example.test/ohjuseong"),
            ("contact", "연락하기", "/about/"),
        ]
        for key, label, url in links:
            SiteLink.objects.get_or_create(
                key=key, defaults={"label": label, "url": url, "original_url": url}
            )

        # 4) 게시글 (공지 + 조롱 글)
        Post.objects.get_or_create(
            title="[공지] 포트폴리오 사이트 오픈",
            defaults={"body": "방문 감사합니다. 피드백은 게시판에 남겨주세요.",
                      "author_name": "운영자", "is_notice": True},
        )
        Post.objects.get_or_create(
            title=MOCK_TITLE,
            defaults={
                "body": "가상 시나리오 단서입니다. 실제 인물/사건과 무관하며, "
                        "조사 시나리오의 시작점으로만 쓰세요.",
                "author_name": "unknown",
                "is_scenario_clue": True,
            },
        )

        # 5) 가상 고객
        for name, email, phone, memo, pw in CUSTOMERS:
            DemoCustomer.objects.get_or_create(
                email=email,
                defaults={"name": name, "phone": phone,
                          "sensitive_memo": memo, "lab_plaintext_password": pw},
            )

        self.stdout.write("seed 완료 (운영자: %s / %s)" % (OPERATOR_ID, OPERATOR_PW))
