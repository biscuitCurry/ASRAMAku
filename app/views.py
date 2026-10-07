import datetime
import json
import logging
import time
from queue import Empty, SimpleQueue

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail, EmailMessage
from django.db import ProgrammingError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import StaffProfileForm, StudentForm
from .models import CheckLog, OutingRequest, OutingTimeSettings, StaffProfile, Student
from .pdf_utils import build_decision_letter_pdf

DASHBOARD_EVENT_SUBSCRIBERS = []
logger = logging.getLogger(__name__)


def get_pending_request_count():
    return OutingRequest.objects.filter(status="Pending").count()

@require_http_methods(["GET"])
def pending_requests_api(request):
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({"error": "Forbidden"}, status=403)

    qs = OutingRequest.objects.filter(status="Pending").select_related("student").order_by("-request_time")
    items = [
        {
            "id": r.id,
            "name": r.student.name,
            "destination": r.destination,
            "time": timezone.localtime(r.request_time).strftime("%b %d, %H:%M"),
        }
        for r in qs[:3]
    ]
    return JsonResponse({"count": qs.count(), "items": items})

@login_required
def my_profile(request):
    profile, _ = StaffProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = StaffProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("my_profile")
    else:
        form = StaffProfileForm(instance=profile)

    return render(
        request, "app/general/profile.html", {"form": form, "profile": profile}
    )


def normalize_time_value(value):
    """Return a real datetime.time object from either string or TimeField data."""
    if value is None:
        return datetime.time(22, 0)
    if isinstance(value, datetime.time):
        return value
    if isinstance(value, str):
        try:
            return datetime.datetime.strptime(value, "%H:%M").time()
        except ValueError:
            try:
                return datetime.datetime.fromisoformat(value).time()
            except ValueError:
                return datetime.time(22, 0)
    if hasattr(value, "time"):
        try:
            return value.time()
        except TypeError:
            pass
    return datetime.time(22, 0)


def get_request_value(request, *names):
    """Read a value from either POST form data or JSON payload."""
    for name in names:
        if request.method == "POST" and name in request.POST:
            return request.POST.get(name)

    if request.body:
        try:
            payload = json.loads(request.body.decode("utf-8"))
            if isinstance(payload, dict):
                for name in names:
                    if name in payload:
                        return payload.get(name)
        except (TypeError, ValueError, UnicodeDecodeError):
            pass

    return None


def get_outing_time_settings():
    """Return the singleton outing-time settings, creating them when needed."""
    try:
        settings, _ = OutingTimeSettings.objects.get_or_create(pk=1)
        return settings
    except ProgrammingError:
        return OutingTimeSettings(pk=1)


def get_checkin_limit_for_datetime(value):
    """Return the allowed check-in cutoff for the given day."""
    return get_outing_time_settings().get_active_curfew_time(value)


def is_late_checkin(check_out_time, check_in_time):
    """Compare the real deadline datetime, not just time-of-day."""
    curfew = get_checkin_limit_for_datetime(check_out_time)
    deadline = timezone.make_aware(
        datetime.datetime.combine(timezone.localtime(check_out_time).date(), curfew)
    )
    if timezone.localtime(check_out_time).time() >= curfew:
        deadline += datetime.timedelta(days=1)
    return check_in_time > deadline


def normalize_identifier(value):
    """Normalize identifier values so lookups are robust to spaces and case."""
    if value is None:
        return ""
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum())


def find_student_by_identifier(identifier):
    """Find a student by student ID, ID card, or RFID UID using a lightning fast DB filter lookup."""
    if identifier is None:
        return None

    search_value = normalize_identifier(identifier)
    if not search_value:
        return None

    # Let the database do the search instantly instead of looping in Python memory
    return Student.objects.filter(
        Q(student_id__iexact=search_value)
        | Q(id_card__iexact=search_value)
        | Q(rfid_uid__iexact=search_value)
    ).first()


def get_current_datetime():
    """Return the current datetime in the configured Django timezone."""
    return timezone.localtime(timezone.now())


def broadcast_dashboard_update():
    """Notify connected dashboard clients that the record state changed."""
    for subscriber in DASHBOARD_EVENT_SUBSCRIBERS:
        try:
            subscriber.put('event: update\ndata: {"type": "record_changed"}\n\n')
        except (BrokenPipeError, OSError, RuntimeError):
            logger.exception("Failed to broadcast dashboard update to a subscriber.")
            continue


def record_check_in(student, check_in_time=None):
    if check_in_time is None:
        check_in_time = get_current_datetime()

    log = (
        student.check_logs.filter(
            check_out_time__isnull=False, check_in_time__isnull=True
        )
        .order_by("-check_out_time")
        .first()
    )

    late = check_in_time > log.return_deadline() if log else False
    student.presence_status = "In"
    student.status = "None"
    student.save()

    if log:
        log.check_in_time = check_in_time
        log.is_late = late
        log.save()
    else:
        log = CheckLog.objects.create(
            student=student, check_in_time=check_in_time, is_late=late
        )

    return log


def notify_student_decision(req, justification=""):
    """Email the student about the decision, with a PDF letter. Never breaks the approval flow."""
    email = req.student.tvetmara_email
    if not email:
        return False

    lines = [
        f"Hi {req.student.name.title()},",
        "",
        f"Your outing request has been {req.status.upper()}.",
        f"Destination: {req.destination}",
        f"Purpose: {req.reason}",
        f"Type: {req.request_type}",
        f"Return by: {req.return_date:%d %b %Y} (by curfew)" if req.return_date else "Return by: same day, by curfew",
        f"Date: {req.outing_date}  Time: {req.outing_time}",
    ]
    if req.status == "Rejected" and justification:
        lines += ["", f"Warden's reason: {justification}"]
    lines += ["", "Your official letter is attached as a PDF.", "", "- ASRAMAku"]

    try:
        msg = EmailMessage(f"Outing request {req.status}", "\n".join(lines), None, [email])
        try:
            now = timezone.localtime(timezone.now())
            pdf = build_decision_letter_pdf(req, now, justification)
            msg.attach(f"outing_{req.status.lower()}_{req.id}.pdf", pdf.getvalue(), "application/pdf")
        except Exception:
            logger.exception("Failed to build decision PDF for request %s", req.id)  # still send the email
        msg.send()
        return True
    except Exception:
        logger.exception("Failed to send decision email to %s", email)
        return False


# -------------------------
# AUTH VIEWS
# -------------------------

def index(request):
    """Home page: staff go to the dashboard, everyone else gets the student permit page."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard")
    return permit_page(request, "index")

# def index(request):
#     """Index/Login page - accessible to everyone"""

#     # If already logged in, redirect to dashboard
#     if request.user.is_authenticated:
#         if request.user.is_staff:
#             return redirect("dashboard")
#         else:
#             return redirect("send_outing_request")

#     # Show login form if not authenticated
#     return render(request, "app/general/index.html")


# def register(request):
#     if request.user.is_authenticated:
#         return redirect('dashboard' if request.user.is_staff else 'send_outing_request')

#     if request.method == "POST":
#         # USE THE NEW SELF-REGISTER FORM HERE:
#         form = StudentSelfRegisterForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Registration successful! You can now check in or request outings.")
#             return redirect("index")
#         else:
#             messages.error(request, "Registration failed. Please check your inputs.")
#     else:
#         form = StudentSelfRegisterForm()

#     return render(request, "app/general/self_register.html", {"form": form})


def login_view(request):
    """Login user from auth_user table"""

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome {user.username}!")

            # Redirect based on user type
            if user.is_staff:
                return redirect("dashboard")  # Staff goes to dashboard
            else:
                return redirect("send_outing_request")  # Students go to outing request
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "app/general/login.html")

    return render(request, "app/general/login.html")


@login_required
def log_out(request):
    logout(request)
    request.session.flush()

    if request.GET.get("close") == "1":
        return HttpResponse(status=204)

    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


@login_required
@user_passes_test(lambda user: user.is_staff)
def outing_time_settings_view(request):
    """Fetch or update the app-wide outing controls."""
    settings = get_outing_time_settings()

    if request.method == "GET":
        curfew_value = settings.get_active_curfew_time()
        return JsonResponse(
            {
                "curfew_time": curfew_value.strftime("%H:%M"),
            }
        )

    if request.method == "POST":
        try:
            curfew_time = get_request_value(request, "curfew_time", "curfewTime")

            if not curfew_time:
                raise ValueError("Curfew time is required.")

            datetime.datetime.strptime(str(curfew_time), "%H:%M")

            settings.curfew_time = normalize_time_value(str(curfew_time))
            settings.save()

            is_ajax = (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.content_type == "application/json"
            )
            if is_ajax:
                return JsonResponse(
                    {"success": True, "message": "Outing settings saved."}
                )

            messages.success(request, "Outing time settings saved successfully.")
            return redirect("dashboard")
        except (TypeError, ValueError):
            message = "Please enter valid values for the outing settings."
            is_ajax = (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.content_type == "application/json"
            )
            if is_ajax:
                return JsonResponse({"success": False, "error": message}, status=400)
            messages.error(request, message)
            return redirect("dashboard")

    return JsonResponse({"error": "Method not allowed."}, status=405)


# -------------------------
# DASHBOARD (CHECK IN / OUT)
# -------------------------


@login_required(login_url="login")
def dashboard(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")

        try:
            student = find_student_by_identifier(student_id)

            if student is None:
                raise Student.DoesNotExist

            # Block banned
            if student.status == "Banned":
                messages.error(request, "Student is banned.")
                return redirect("dashboard")

            if student.presence_status == "In":
                student.presence_status = "Out"
                student.save()

                today = timezone.localdate()
                approved = (
                    OutingRequest.objects.filter(
                        student=student,
                        status="Approved",
                        request_type="Home Leave",
                        outing_date__lte=today,
                        return_date__gte=today,
                    )
                    .order_by("-request_time")
                    .first()
                )
                CheckLog.objects.create(
                    student=student, check_out_time=get_current_datetime(), outing_request=approved
                )
                if approved:
                    approved.status = "Used"
                    approved.save(update_fields=["status"])

                broadcast_dashboard_update()
                messages.success(request, f"{student.name} checked out successfully.")

            elif student.presence_status == "Out":
                check_in_time = get_current_datetime()
                log = record_check_in(student, check_in_time)

                broadcast_dashboard_update()

                if log.is_late:
                    deadline = timezone.localtime(log.return_deadline())
                    messages.warning(
                        request,
                        f"Late check-in notice: {student.name} returned after the {deadline:%d %b, %I:%M %p} deadline.",
                    )
                else:
                    messages.success(
                        request, f"{student.name} checked in successfully."
                    )

        except Student.DoesNotExist:
            messages.error(request, "Student not found.")

        return redirect("dashboard")

    # ==========================================
    # GET REQUEST: DATE PARSING & FILTER LOGIC
    # ==========================================
    date_str = request.GET.get("date")
    today = timezone.localdate()

    selected_date = today
    if date_str:
        try:
            selected_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            selected_date = today

    # Calculate dates for controls
    # prev_date_str = (selected_date - timedelta(days=1)).strftime("%Y-%m-%d")
    # next_date_str = (selected_date + timedelta(days=1)).strftime("%Y-%m-%d")
    # today_str = today.strftime("%Y-%m-%d")
    selected_date_str = selected_date.strftime("%Y-%m-%d")
    # is_today = (selected_date == today)

    # Calculate timezone-aware start and end datetimes for the selected local day
    start_datetime = timezone.make_aware(
        datetime.datetime.combine(selected_date, datetime.time.min)
    )
    end_datetime = timezone.make_aware(
        datetime.datetime.combine(selected_date, datetime.time.max)
    )

    present_count = (
        Student.objects.filter(presence_status="In").exclude(status="Banned").count()
    )

    settings = get_outing_time_settings()
    curfew_time = settings.get_active_curfew_time(today)
    curfew_datetime = timezone.make_aware(datetime.datetime.combine(today, curfew_time))
    late_count = (
        CheckLog.objects.filter(
            student__presence_status="In",
            check_in_time__gt=curfew_datetime,
            check_in_time__lte=timezone.make_aware(
                datetime.datetime.combine(today, datetime.time.max)
            ),
        )
        .values("student_id")
        .distinct()
        .count()
    )
    approved_count = OutingRequest.objects.filter(
        status="Approved", outing_date=today
    ).count()

    # ⚡ OPTIMIZATION 1: Fetch check logs along with student data in 1 single query
    logs = CheckLog.objects.filter(
        Q(check_out_time__range=(start_datetime, end_datetime))
        | Q(check_in_time__range=(start_datetime, end_datetime))
    ).select_related("student", "outing_request")

    # ⚡ OPTIMIZATION 2: Get all active approved outings in ONE query instead of inside a loop
    student_ids = [log.student_id for log in logs]
    approved_outings = OutingRequest.objects.filter(
        student_id__in=student_ids, status="Approved"
    ).order_by("request_time")

    # Map student IDs to their last approved request for instant memory lookup
    outing_map = {outing.student_id: outing.status for outing in approved_outings}

    log_entries = []
    for log in logs:
        student = log.student

        # ⚡ OPTIMIZATION 3: Instant dictionary lookup replaces the slow database loop hit
        request_status = outing_map.get(student.id, "None")

        log_entries.append(
            {
                "student": student,
                "log": log,
                "request_status": request_status,
                "is_late": bool(log.is_late),
            }
        )

    # Sort log entries newest first based on activity times
    log_entries.sort(
        key=lambda item: (
            item["log"].check_out_time or item["log"].check_in_time or timezone.now(),
            item["log"].check_in_time or item["log"].check_out_time or timezone.now(),
        ),
        reverse=True,
    )

    return render(
        request,
        "app/general/dashboard.html",
        {
            "log_entries": log_entries,
            "selected_date_str": selected_date_str,
            "present_count": present_count,
            "late_count": late_count,
            "approved_count": approved_count,
            # "prev_date_str": prev_date_str,
            # "next_date_str": next_date_str,
            # "today_str": today_str,
            # "is_today": is_today,
        },
    )


# -------------------------
# CRUD (STAFF ONLY)
# -------------------------


def is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def add_student(request):
    """Add a new student"""
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully.")
            return redirect("manage_students")
    else:
        form = StudentForm()

    return render(request, "app/general/add_student.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_student(request, pk):
    """Edit an existing student"""
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student updated successfully.")
            return redirect("manage_students")
    else:
        form = StudentForm(instance=student)

    return render(
        request, "app/general/edit_student.html", {"form": form, "student": student}
    )


@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_student(request, pk):
    """Delete a student"""
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        student.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect("manage_students")

    return render(request, "app/general/delete_student.html", {"student": student})


@login_required
@user_passes_test(lambda u: u.is_staff)
def manage_students(request):
    """View all students and manage them - Fast & stable"""
    # 'user' is the only relational field on Student, so we prefetch it[cite: 3].
    # 'course' and 'session' are plain text fields, so they load instantly[cite: 3].
    students = Student.objects.select_related("user").all().order_by("name")
    return render(request, "app/general/manage_students.html", {"students": students})


# -------------------------
# OUTING REQUESTS (STUDENT ONLY)
# -------------------------

def verify_student_identity(student_id, id_card=None):
    """Look a student up by matric ID only (IC check removed)."""
    matric = str(student_id or "").strip()
    if not matric:
        return None
    return Student.objects.filter(student_id__iexact=matric).first()


@require_http_methods(["POST"])
def verify_student(request):
    """Student portal step 1: check matric ID + IC, return profile and recent requests."""
    student = verify_student_identity(request.POST.get("student_id"), request.POST.get("id_card"))
    if student is None:
        return JsonResponse({"error": "Matric ID not found. Please check and try again."}, status=404)

    recent = student.outing_requests.order_by("-request_time")[:3]
    return JsonResponse({
        "name": student.name,
        "course": student.course,
        "session": student.session,
        "requests": [
            {
                "destination": r.destination,
                "dates": " to ".join(d.strftime("%d %b") for d in (r.outing_date, r.return_date) if d),
                "status": r.status,
            }
            for r in recent
        ],
    })


def permit_page(request, redirect_name):
    """Student home leave permit form (outings don't need a permit)."""

    if request.method == "POST":
        student = verify_student_identity(request.POST.get("student_id"), request.POST.get("id_card"))
        if student is None:
            messages.error(request, "Matric ID and IC number do not match our records.")
            return redirect(redirect_name)

        destination = (request.POST.get("destination") or "").strip()
        reason = (request.POST.get("reason") or "").strip()
        outing_date = request.POST.get("outing_date")
        outing_time = request.POST.get("outing_time")
        return_date = request.POST.get("return_date")

        cfg, _ = OutingTimeSettings.objects.get_or_create(pk=1)
        try:
            start = datetime.date.fromisoformat(outing_date)
            end = datetime.date.fromisoformat(return_date)
            datetime.time.fromisoformat(outing_time)
        except (TypeError, ValueError):
            start = end = None

        if not destination or not reason or not start or not end:
            messages.error(request, "Please fill in every field of the home leave form.")
            return redirect(redirect_name)
        if end < start:
            messages.error(request, "Home leave needs a return date after the leave date.")
            return redirect(redirect_name)
        if (end - start).days > cfg.max_home_leave_days:
            messages.error(request, f"Home leave cannot be longer than {cfg.max_home_leave_days} days.")
            return redirect(redirect_name)

        OutingRequest.objects.create(
            student=student,
            request_type="Home Leave",
            destination=destination,
            reason=reason,
            outing_date=outing_date,
            outing_time=outing_time,
            return_date=return_date,
            status="Pending",
        )
        broadcast_dashboard_update()
        messages.success(request, "Home leave request submitted. You'll get an email once the warden decides.")
        return redirect(redirect_name)

    return render(request, "app/general/index.html")


def send_outing_request(request):
    """Same permit page at /outing/send/ (used by the staff 'Test Form' link)."""
    return permit_page(request, "send_outing_request")

# def send_outing_request(request):
#     """Student submits a home leave request (outings don't need a permit)"""

#     if request.method == "POST":
#         student_id = request.POST.get("student_id")
#         request_type = "Home Leave"  # outings don't need a permit
#         destination = request.POST.get("destination")
#         reason = request.POST.get("reason")
#         outing_date = request.POST.get("outing_date")
#         outing_time = request.POST.get("outing_time")
#         return_date = request.POST.get("return_date") or None

#         cfg, _ = OutingTimeSettings.objects.get_or_create(pk=1)
#         try:
#             start = datetime.date.fromisoformat(outing_date)
#             end = datetime.date.fromisoformat(return_date) if return_date else None
#         except (TypeError, ValueError):
#             start = end = None

#         if not start or not end or end <= start:
#             messages.error(request, "Home leave needs a return date after the leave date.")
#             return redirect("send_outing_request")
#         if (end - start).days > cfg.max_home_leave_days:
#             messages.error(request, f"Home leave cannot be longer than {cfg.max_home_leave_days} days.")
#             return redirect("send_outing_request")

#         try:
#             student = Student.objects.get(student_id=student_id)
#             OutingRequest.objects.create(
#                 student=student,
#                 request_type=request_type,
#                 destination=destination,
#                 reason=reason,
#                 outing_date=outing_date,
#                 outing_time=outing_time,
#                 return_date=return_date,
#                 status="Pending",
#             )
#             broadcast_dashboard_update()
#             messages.success(request, "Home leave request submitted successfully!")
#         except Student.DoesNotExist:
#             messages.error(request, "Student not found.")

#         return redirect("send_outing_request")

#     return render(request, "app/general/outing_request.html")


def decide_request(pk, new_status, justification=""):
    """Approve or reject a request exactly once.

    The filter + update runs as a single database statement, so when several clicks
    arrive together only the first one finds the request still Pending. The rest get None.
    """
    claimed = OutingRequest.objects.filter(pk=pk, status="Pending").update(status=new_status)
    if not claimed:
        return None

    req = OutingRequest.objects.select_related("student").get(pk=pk)
    req.student.status = new_status
    req.student.save(update_fields=["status"])
    req.emailed = notify_student_decision(req, justification)
    return req


@login_required
@user_passes_test(lambda u: u.is_staff)
def manage_outing_requests(request):
    """Manage outing requests with bulk actions"""

    if request.method == "POST":
        action = request.POST.get("action")
        request_ids = request.POST.getlist("request_ids")
        justification = request.POST.get("justification", "").strip()

        if not request_ids:
            messages.error(request, "Please select at least one request.")
            return redirect("manage_requests")
        if action not in ("approve", "reject"):
            return redirect("manage_requests")

        new_status = "Approved" if action == "approve" else "Rejected"
        done = sum(1 for pk in request_ids if decide_request(pk, new_status, justification))
        skipped = len(request_ids) - done

        messages.success(
            request,
            f"{done} request(s) {new_status.lower()}."
            + (f" {skipped} already decided, skipped." if skipped else ""),
        )
        return redirect("manage_requests")

    requests = OutingRequest.objects.filter(status="Pending").order_by("-request_time")
    return render(request, "app/general/manage_requests.html", {"requests": requests})


@login_required
@user_passes_test(lambda u: u.is_staff)
def approve_request(request, pk):
    """Approve a single request"""
    get_object_or_404(OutingRequest, id=pk)
    req = decide_request(pk, "Approved")

    if req is None:
        messages.info(request, "That request was already decided. No email was sent again.")
    else:
        messages.success(
            request,
            f"Request from {req.student.name} approved."
            + ("" if req.emailed else " (No email sent.)"),
        )
    return redirect("manage_requests")


@login_required
@user_passes_test(lambda u: u.is_staff)
def reject_request(request, pk):
    """Reject a single request with a mandatory justification"""
    get_object_or_404(OutingRequest, id=pk)

    if request.method == "POST":
        justification = request.POST.get("justification", "").strip()

        if not justification:
            messages.error(
                request, "You must provide a justification text to reject this request."
            )
            return redirect("manage_requests")

        req = decide_request(pk, "Rejected", justification)
        if req is None:
            messages.info(request, "That request was already decided. No email was sent again.")
        else:
            messages.info(
                request,
                f"Request from {req.student.name} rejected. Reason: {justification}"
                + ("" if req.emailed else " (No email sent.)"),
            )

    return redirect("manage_requests")


@login_required
@user_passes_test(lambda u: u.is_staff)
def view_request(request, pk):
    """View request details"""
    req = get_object_or_404(OutingRequest, id=pk)
    return render(request, "app/general/view_request.html", {"request": req})


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET"])
def get_student_by_id(request, student_id):
    """API endpoint to fetch student details"""
    try:
        student = Student.objects.get(student_id=student_id)
        return JsonResponse(
            {
                "id": student.id,
                "name": student.name,
                "course": student.course,
                "session": student.session,
            }
        )
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)


@require_http_methods(["GET"])
def server_time(request):
    """Return the current server time for synchronized dashboard display."""
    now = timezone.localtime(timezone.now())
    return JsonResponse({"server_time": now.strftime("%Y-%m-%d %H:%M:%S")})


@require_http_methods(["GET"])
def dashboard_updates(request):
    """Return a lightweight snapshot so the dashboard can refresh on real changes."""
    students = Student.objects.all()
    snapshot = []
    for student in students:
        latest_log = student.check_logs.order_by(
            "-check_in_time", "-check_out_time"
        ).first()
        snapshot.append(
            {
                "id": student.id,
                "presence_status": student.presence_status,
                "last_log_id": latest_log.id if latest_log else None,
                "last_log_updated": latest_log.check_in_time
                or latest_log.check_out_time
                if latest_log
                else None,
            }
        )

    now = timezone.localtime(timezone.now())
    return JsonResponse(
        {
            "snapshot": snapshot,
            "server_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def dashboard_events(request):
    """Stream dashboard update events to the browser when records change."""

    def event_stream():
        subscriber = SimpleQueue()
        DASHBOARD_EVENT_SUBSCRIBERS.append(subscriber)
        started = last_ping = time.monotonic()
        try:
            yield "retry: 3000\n\n"
            while time.monotonic() - started < 120:  # recycle every 2 min
                try:
                    yield subscriber.get(timeout=1)
                except Empty:
                    if time.monotonic() - last_ping >= 15:
                        last_ping = time.monotonic()
                        yield ": ping\n\n"  # lets the server notice closed tabs
        except GeneratorExit:
            pass
        finally:
            if subscriber in DASHBOARD_EVENT_SUBSCRIBERS:
                DASHBOARD_EVENT_SUBSCRIBERS.remove(subscriber)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
