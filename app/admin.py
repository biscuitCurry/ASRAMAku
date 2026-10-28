from django.contrib import admin

from .models import Ban, CheckLog, OutingRequest, Student

@admin.action(description="Approve selected students")
def approve_exit(modeladmin, request, queryset):
    queryset.update(status="Approved")


@admin.action(description="Disapprove selected students")
def disapprove_exit(modeladmin, request, queryset):
    queryset.update(status="Rejected")


@admin.action(description="Ban selected students (until lifted)")
def ban_students(modeladmin, request, queryset):
    banned = 0
    for student in queryset:
        if not student.active_ban:
            Ban.objects.create(student=student, reason="Banned from the admin site.", banned_by=request.user)
            banned += 1
    modeladmin.message_user(request, f"Banned {banned} student(s). Set an end date or lift it under Bans.")

@admin.action(description="Delete selected log entries permanently")
def delete_logs(modeladmin, request, queryset):
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(
        request, f"Successfully deleted {count} check log record(s)."
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "student_id",
        "course",
        "session",
        "status",
        "presence_status",
    )
    search_fields = ("name", "student_id")
    list_filter = ("status", "course", "session")

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.actions = [approve_exit, disapprove_exit]


@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
    list_display = ("student", "reason", "starts_at", "ends_at", "banned_by", "lifted_at")
    search_fields = ("student__name", "student__student_id", "reason")
    list_filter = ("starts_at", "lifted_at")
    raw_id_fields = ("student",)


@admin.register(CheckLog)
class CheckLogAdmin(admin.ModelAdmin):
    list_display = ("student", "check_out_time", "check_in_time")
    readonly_fields = ("student", "check_out_time", "check_in_time")

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.actions = [delete_logs]


@admin.register(OutingRequest)
class OutingRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "destination", "outing_date", "status", "request_time")
    search_fields = ("name", "destination")
    list_filter = ("status", "outing_date")

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.actions = [approve_exit, disapprove_exit, ban_students]
