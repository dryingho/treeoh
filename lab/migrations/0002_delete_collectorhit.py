from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("lab", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="CollectorHit",
        ),
    ]
