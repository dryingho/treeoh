import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from board.models import Comment, Post
from demo_records.models import DemoCustomer
from lab.models import CollectorHit
from operator_panel.models import AuditLog
from portfolio.models import Project, SiteLink
from uploads.models import UploadRecord


class Command(BaseCommand):
    help = "실습 데이터와 업로드 파일을 지운다"

    def add_arguments(self, parser):
        parser.add_argument("--seed", action="store_true", help="지운 뒤 다시 seed")

    def handle(self, *args, **options):
        # 1) DB 데이터 지우기 (이 프로젝트 것만)
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Project.objects.all().delete()
        SiteLink.objects.all().delete()
        DemoCustomer.objects.all().delete()
        UploadRecord.objects.all().delete()
        AuditLog.objects.all().delete()
        CollectorHit.objects.all().delete()

        # 2) 업로드/증거 파일 지우기
        for sub in ["avatars", "_evidence"]:
            folder = os.path.join(str(settings.MEDIA_ROOT), sub)
            if os.path.isdir(folder):
                for name in os.listdir(folder):
                    if name == ".gitkeep":
                        continue
                    try:
                        os.remove(os.path.join(folder, name))
                    except OSError:
                        pass

        # 3) 수집기 로그 지우기
        log = str(settings.LAB_COLLECTOR_LOG)
        if os.path.exists(log):
            try:
                os.remove(log)
            except OSError:
                pass

        self.stdout.write("초기화 완료")
        if options["seed"]:
            call_command("seed_lab")
