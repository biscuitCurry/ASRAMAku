import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def move_old_bans(apps, schema_editor):
    """Students marked "Banned" the old way become an open-ended Ban (until lifted)."""
    Student = apps.get_model("app", "Student")
    Ban = apps.get_model("app", "Ban")
    for student in Student.objects.filter(status="Banned"):
        Ban.objects.create(student=student, reason="Banned before the ban system was added.")
    Student.objects.filter(status="Banned").update(status="None")


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0020_staffprofile_email_notifications"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Ban",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.TextField()),
                ("starts_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("ends_at", models.DateTimeField(blank=True, null=True, help_text="Leave empty to ban until lifted by hand.")),
                ("lifted_at", models.DateTimeField(blank=True, null=True)),
                ("banned_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bans_given", to=settings.AUTH_USER_MODEL)),
                ("lifted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bans_lifted", to=settings.AUTH_USER_MODEL)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bans", to="app.student")),
            ],
            options={"ordering": ["-starts_at"]},
        ),
        migrations.RunPython(move_old_bans, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="student",
            name="status",
            field=models.CharField(
                choices=[("None", "None"), ("Approved", "Approved"), ("Rejected", "Rejected")],
                default="None",
                max_length=20,
            ),
        ),
    ]