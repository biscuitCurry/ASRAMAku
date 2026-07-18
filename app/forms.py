from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, OutingRequest


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


# In your forms.py file:

class StudentSelfRegisterForm(forms.ModelForm):
    class Meta:
        model = Student
        # ONLY include the fields that the student actually fills out on the webpage!
        fields = ["name", "course", "session", "student_id", "id_card", "rfid_uid"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "course": forms.TextInput(attrs={"class": "form-control", "placeholder": "Course"}),
            "session": forms.TextInput(attrs={"class": "form-control", "placeholder": "Session (e.g., JUL-DIS 2024)"}),
            "student_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "Matric ID"}),
            "id_card": forms.TextInput(attrs={"class": "form-control", "placeholder": "ID Card Number"}),
            "rfid_uid": forms.TextInput(attrs={"class": "form-control", "placeholder": "RFID UID"}),
        }

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["name", "course", "session", "student_id", "id_card", "rfid_uid", "status", "presence_status", "user"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "course": forms.TextInput(attrs={"class": "form-control", "placeholder": "Course"}),
            "session": forms.TextInput(attrs={"class": "form-control", "placeholder": "Session (e.g., JUL-DIS 2024)"}),
            "student_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "Matric ID"}),
            "id_card": forms.TextInput(attrs={"class": "form-control", "placeholder": "ID Card Number"}),
            "rfid_uid": forms.TextInput(attrs={"class": "form-control", "placeholder": "RFID UID"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "presence_status": forms.Select(attrs={"class": "form-control"}),
            "user": forms.Select(attrs={"class": "form-control"}),
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