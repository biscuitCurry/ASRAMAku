from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("", views.index, name="index"),
    path("register/", views.register, name="register"),
    path("login/", views.log_in, name="login"),
    path("logout/", views.log_out, name="logout"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # CRUD
    path("student/add/", views.add_student, name="add_student"),
    path("student/edit/<int:pk>/", views.edit_student, name="edit_student"),
    path("student/delete/<int:pk>/", views.delete_student, name="delete_student"),

    # Outing Requests
    path("outing/send/", views.send_outing_request, name="send_outing_request"),
    path("outing/manage/", views.manage_outing_requests, name="manage_requests"),
    path("outing/approve/<int:pk>/", views.approve_request, name="approve_request"),
    path("outing/reject/<int:pk>/", views.reject_request, name="reject_request"),

    # API
    path('api/student/<str:student_id>/', views.get_student_by_id, name='get_student'),
]