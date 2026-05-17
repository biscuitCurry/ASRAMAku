from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),  # Root path goes to index (login page)
    path("login/", views.login_view, name="login"),
    path("logout/", views.log_out, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("student/add/", views.add_student, name="add_student"),
    path("student/edit/<int:pk>/", views.edit_student, name="edit_student"),
    path("student/delete/<int:pk>/", views.delete_student, name="delete_student"),

    path("outing/send/", views.send_outing_request, name="send_outing_request"),
    path("outing/manage/", views.manage_outing_requests, name="manage_requests"),
    path("outing/approve/<int:pk>/", views.approve_request, name="approve_request"),
    path("outing/reject/<int:pk>/", views.reject_request, name="reject_request"),
    path('outing/view/<int:pk>/', views.view_request, name='view_request'),

    path('api/student/<str:student_id>/', views.get_student_by_id, name='get_student'),
    path('students/', views.manage_students, name='manage_students'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/edit/<int:pk>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:pk>/', views.delete_student, name='delete_student'),
]