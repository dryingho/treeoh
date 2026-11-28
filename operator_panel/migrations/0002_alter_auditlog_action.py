from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operator_panel", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("link_change", "사이트 링크 변경"),
                    ("profile_update", "프로필 수정"),
                    ("login", "로그인"),
                    ("login_failed", "로그인 실패"),
                    ("avatar_upload", "프로필 사진 업로드"),
                    ("project_update", "대표 프로젝트 수정"),
                ],
                max_length=40,
            ),
        ),
    ]
