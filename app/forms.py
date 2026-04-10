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
        fields = "__all__"


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