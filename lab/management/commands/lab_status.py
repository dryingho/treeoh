import os

from django.conf import settings
from django.core.management.base import BaseCommand

from board.models import Comment, Post
from demo_records.models import DemoCustomer
from operator_panel.models import AuditLog
from uploads.models import UploadRecord


class Command(BaseCommand):
    help = "지금 실습 상태(모드/흔적 수)를 보여준다"

    def handle(self, *args, **options):
        # 스크립트성 댓글 수
        script_comments = 0
        for c in Comment.objects.all():
            if c.looks_like_script:
                script_comments += 1

        # 증거 파일 목록
        evidence_dir = os.path.join(str(settings.MEDIA_ROOT), "_evidence")
        files = []
        if os.path.isdir(evidence_dir):
            files = [f for f in sorted(os.listdir(evidence_dir)) if not f.startswith(".")]

        p = self.stdout.write
        p("====== 실습 상태 ======")
        p("모드: %s" % settings.LAB_MODE)
        p("댓글 그대로 출력(XSS): %s" % settings.LAB_COMMENTS_RENDER_SAFE)
        p("세션 쿠키 HttpOnly   : %s" % settings.SESSION_COOKIE_HTTPONLY)
        p("업로드 이미지 검사   : %s" % settings.LAB_UPLOAD_VALIDATE_IMAGE)
        p("-----------------------")
        p("게시글: %d" % Post.objects.count())
        p("댓글  : %d (스크립트성 %d)" % (Comment.objects.count(), script_comments))
        p("업로드 실행 후보 : %d" % UploadRecord.objects.filter(is_executable_candidate=True).count())
        p("가상 고객        : %d" % DemoCustomer.objects.count())
        p("활동 기록        : %d" % AuditLog.objects.count())
        p("-----------------------")
        p("증거 파일: %s" % (", ".join(files) if files else "없음"))
