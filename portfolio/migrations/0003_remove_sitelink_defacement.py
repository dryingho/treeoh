from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("portfolio", "0002_project_link"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sitelink",
            name="original_url",
        ),
        migrations.RemoveField(
            model_name="sitelink",
            name="is_defaced",
        ),
    ]
