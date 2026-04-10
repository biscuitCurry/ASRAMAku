from django.contrib import admin
from .models import CheckLog, Student, OutingRequest


@admin.action(description="Approve selected students")
def approve_exit(modeladmin, request, queryset):
    queryset.update(status="Approved")


@admin.action(description="Disapprove selected students")
def disapprove_exit(modeladmin, request, queryset):
    queryset.update(status="Rejected")


@admin.action(description="Ban selected students")
def ban_students(modeladmin, request, queryset):
    queryset.update(status="Banned")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "student_id", "course", "session", "status", "presence_status")
    search_fields = ("name", "student_id")
    list_filter = ("status", "course", "session")
    actions = [approve_exit, disapprove_exit, ban_students]

@admin.register(CheckLog)
class CheckLogAdmin(admin.ModelAdmin):
    list_display = ("student", "check_out_time", "check_in_time")
    readonly_fields = ("student", "check_out_time", "check_in_time")

@admin.register(OutingRequest)
class OutingRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "destination", "outing_date", "status", "request_time")
    search_fields = ("name", "destination")
    list_filter = ("status", "outing_date")
    actions = [approve_exit, disapprove_exit, ban_students]
