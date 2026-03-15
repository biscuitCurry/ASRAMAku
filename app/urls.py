from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("register/", views.register, name="register"),
    path("login/", views.log_in, name="login"),
    path("logout/", views.log_out, name="logout"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # CRUD
    path("student/add/", views.add_student, name="add_student"),
    path("student/edit/<int:pk>/", views.edit_student, name="edit_student"),
    path("student/delete/<int:pk>/", views.delete_student, name="delete_student"),
]