import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_uppercase_student_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='OutingTimeSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('curfew_time', models.TimeField(default=datetime.time(22, 0))),
                ('max_outing_duration_hours', models.PositiveIntegerField(default=4)),
                ('late_threshold_minutes', models.PositiveIntegerField(default=15)),
            ],
            options={
                'verbose_name': 'Outing Time Settings',
                'verbose_name_plural': 'Outing Time Settings',
            },
        ),
    ]
