import hashlib

from django.db import migrations, models


def hash_existing(apps, schema_editor):
    Auth = apps.get_model("users", "auth")
    for row in Auth.objects.all():
        row.token_hash = hashlib.sha256(row.token_hash.encode()).hexdigest()
        row.save(update_fields=["token_hash"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_user_language_user_phone_alter_user_user_type"),
    ]

    operations = [
        migrations.RenameField(model_name="auth", old_name="refresh_token", new_name="token_hash"),
        migrations.RunPython(hash_existing, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="auth",
            name="token_hash",
            field=models.CharField(max_length=64, unique=True),
        ),
    ]
