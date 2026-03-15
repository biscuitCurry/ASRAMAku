from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# Create your models here.

class Student(models.Model):
    name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    session = models.CharField(max_length=20)
    student_id = models.CharField(max_length=12, unique=True)
    id_card = models.CharField(max_length=50, unique=True)
    rfid_uid = models.CharField(max_length=50, unique=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name="student_profile")

    status = models.CharField(
        max_length=20,
        choices=[
            ("None", "None"),
            ("Approved", "Approved"),
            ("Rejected", "Rejected"),
            ("Banned", "Banned"),
        ],
        default="None"
    )

    presence_status = models.CharField(
    max_length=10,
    choices=[
        ("In", "In"),
        ("Out", "Out"),
    ],
    default="In"
    )

    def __str__(self):
        return f"{self.name} ({self.student_id})"
    

class CheckLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="check_logs")
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - Log"
    
class OutingRequest(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE)

    reason = models.TextField()
    destination = models.CharField(max_length=255)

    request_time = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    def __str__(self):
        return f"{self.student.username} - {self.status}"