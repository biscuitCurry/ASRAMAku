from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, OutingRequest


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["name", "course", "session", "student_id", "id_card", "rfid_uid", "address", "phone_number", "tvetmara_email", "parent_contact"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control text-uppercase", "placeholder": "Full Name"}),
            "course": forms.TextInput(attrs={"class": "form-control text-uppercase", "placeholder": "Course"}),
            "session": forms.TextInput(attrs={"id": "session-input", "class": "form-control", "placeholder": "Session (e.g., JUL-DIS 2024)"}),
            "student_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "Matric ID (e.g., 1234567890)"}),
            "id_card": forms.TextInput(attrs={"class": "form-control", "placeholder": "IC Number"}),
            "rfid_uid": forms.TextInput(attrs={"class": "form-control", "placeholder": "RFID UID (Tap your IC on RFID scanner)"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Address"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
            "tvetmara_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "TVETMARA Email (e.g., student@sgpetani.tvetmara.edu.my)"}),
            "parent_contact": forms.TextInput(attrs={"class": "form-control", "placeholder": "Parent/Guardian Contact"}),
        }


class OutingRequestForm(forms.ModelForm):
    class Meta:
        model = OutingRequest
        fields = ["destination", "reason", "outing_date", "outing_time"]
        widgets = {
            "destination": forms.TextInput(attrs={"class": "form-control", "placeholder": "Where are you going?"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Why do you need to go out?"}),
            "outing_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "outing_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
        }