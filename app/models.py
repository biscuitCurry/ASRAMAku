from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class Student(models.Model):
    name = models.CharField("Name", max_length=100)
    course = models.CharField("Course", max_length=100)
    session = models.CharField("Session", max_length=20)
    student_id = models.CharField("Matric ID", max_length=12, unique=True)
    id_card = models.CharField("IC Number", max_length=50, unique=True)
    rfid_uid = models.CharField("RFID UID", max_length=50, unique=True)
    phone_number = models.CharField("Phone Number", max_length=20, blank=True, null=True)
    tvetmara_email = models.EmailField("TVETMARA E-MAIL", blank=True, null=True)
    address = models.TextField("Address", blank=True, null=True)
    parent_contact = models.CharField("Parent/Guardian Contact", max_length=20, blank=True, null=True)

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
        return self.name
    

class CheckLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="check_logs")
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.name} - Log"
    
class OutingRequest(models.Model):

    STATUS_CHOICES = [
    ("Pending", "Pending"),
    ("Approved", "Approved"),
    ("Rejected", "Rejected"),
    ("Used", "Used"),   # 🔥 NEW
]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="outing_requests")
    destination = models.CharField(max_length=255)
    reason = models.TextField()
    outing_date = models.DateField(null=True, blank=True)
    outing_time = models.TimeField(null=True, blank=True)
    request_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    def __str__(self):
        return f"{self.student.name} - {self.destination} ({self.status})"
    
class SystemSettings(models.Model):
    is_simulation_active = models.BooleanField(default=False, verbose_name="Enable Time Simulation")
    simulated_datetime = models.DateTimeField(blank=True, null=True, verbose_name="Simulated System Time")

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return "System Configuration Override"