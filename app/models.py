import datetime

from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class OutingTimeSettings(models.Model):
    curfew_time = models.TimeField(default=datetime.time(22, 0))
    max_outing_duration_hours = models.PositiveIntegerField(default=4)
    late_threshold_minutes = models.PositiveIntegerField(default=15)

    class Meta:
        verbose_name = "Outing Time Settings"
        verbose_name_plural = "Outing Time Settings"

    def __str__(self):
        return "Outing Time Settings"


class Student(models.Model):
    name = models.CharField("Name", max_length=100)
    course = models.CharField("Course", max_length=100)
    session = models.CharField("Session", max_length=20)
    student_id = models.CharField("Matric ID", max_length=12, unique=True)
    id_card = models.CharField("IC Number", max_length=50, unique=True)
    rfid_uid = models.CharField("RFID UID", max_length=50, unique=True)
    phone_number = models.CharField(
        "Phone Number", max_length=20, blank=True, null=True
    )
    tvetmara_email = models.EmailField("TVETMARA E-MAIL", blank=True, null=True)
    address = models.TextField("Address", blank=True, null=True)
    parent_contact = models.CharField(
        "Parent/Guardian Contact", max_length=20, blank=True, null=True
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="student_profile",
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("None", "None"),
            ("Approved", "Approved"),
            ("Rejected", "Rejected"),
            ("Banned", "Banned"),
        ],
        default="None",
    )

    presence_status = models.CharField(
        max_length=10,
        choices=[
            ("In", "In"),
            ("Out", "Out"),
        ],
        default="In",
    )

    def save(self, *args, **kwargs):
        # Ensure the student's name is stored uppercase
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CheckLog(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="check_logs"
    )
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.name} - Log"


class OutingRequest(models.Model):
    # Use an immutable tuple for choices to avoid mutable class attribute
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Used", "Used"),
    )

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="outing_requests"
    )
    destination = models.CharField(max_length=255)
    reason = models.TextField()
    outing_date = models.DateField(null=True, blank=True)
    outing_time = models.TimeField(null=True, blank=True)
    request_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")

    def __str__(self):
        return f"{self.student.name} - {self.destination} ({self.status})"
