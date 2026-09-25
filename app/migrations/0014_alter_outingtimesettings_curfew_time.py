from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0013_outingtimesettings"),
    ]

    operations = [
        migrations.AlterField(
            model_name="outingtimesettings",
            name="curfew_time",
            field=models.TimeField(blank=True, default=None, null=True),
        ),
    ]
