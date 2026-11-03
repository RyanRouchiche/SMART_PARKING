import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_hash_refresh_tokens"),
    ]

    operations = [
        migrations.RenameModel(old_name="auth", new_name="RefreshSession"),
        migrations.AlterField(
            model_name="refreshsession",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="refresh_session",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
