from django.db import migrations


def uppercase_student_names(apps, schema_editor):
    Student = apps.get_model('app', 'Student')
    for student in Student.objects.all():
        if student.name:
            student.name = student.name.upper()
            student.save(update_fields=['name'])


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_delete_systemsettings'),
    ]

    operations = [
        migrations.RunPython(uppercase_student_names, reverse_code=migrations.RunPython.noop),
    ]
