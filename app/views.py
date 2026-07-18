from queue import Empty, SimpleQueue
from datetime import time, datetime, timedelta

from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .forms import RegisterForm, StudentForm, OutingRequestForm, StudentSelfRegisterForm
from .models import Student, CheckLog, OutingRequest


DASHBOARD_EVENT_SUBSCRIBERS = []


def get_checkin_limit_for_datetime(value):
    """Return the allowed check-in cutoff for the given day."""
    return time(19, 0) if value.weekday() in {0, 1, 2, 3, 6} else time(22, 0)


def is_late_checkin(check_in_time):
    """Return True if the student checked in after the permitted time."""
    limit = get_checkin_limit_for_datetime(check_in_time)
    return check_in_time.time() > limit


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
        Q(student_id__iexact=search_value) | 
        Q(id_card__iexact=search_value) | 
        Q(rfid_uid__iexact=search_value)
    ).first()


def get_current_datetime():
    """Return the current datetime in the configured Django timezone."""
    return timezone.localtime(timezone.now())


def broadcast_dashboard_update():
    """Notify connected dashboard clients that the record state changed."""
    for subscriber in list(DASHBOARD_EVENT_SUBSCRIBERS):
        try:
            subscriber.put('event: update\ndata: {"type": "record_changed"}\n\n')
        except Exception:
            continue


def record_check_in(student, check_in_time=None):
    """Close the latest open exit record and mark it with the enter time."""
    if check_in_time is None:
        check_in_time = get_current_datetime()

    student.presence_status = "In"
    student.status = "None"
    student.save()

    late = is_late_checkin(check_in_time)
    log = student.check_logs.filter(check_out_time__isnull=False, check_in_time__isnull=True).order_by('-check_out_time').first()

    if log:
        log.check_in_time = check_in_time
        log.is_late = late
        log.save()
    else:
        log = CheckLog.objects.create(
            student=student,
            check_in_time=check_in_time,
            is_late=late,
        )

    return log


# -------------------------
# AUTH VIEWS
# -------------------------

def index(request):
    """Index/Login page - accessible to everyone"""
    
    # If already logged in, redirect to dashboard
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('dashboard')
        else:
            return redirect('send_outing_request')
    
    # Show login form if not authenticated
    return render(request, "app/general/index.html")

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard' if request.user.is_staff else 'send_outing_request')

    if request.method == "POST":
        # USE THE NEW SELF-REGISTER FORM HERE:
        form = StudentSelfRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! You can now check in or request outings.")
            return redirect("index")
        else:
            messages.error(request, "Registration failed. Please check your inputs.")
    else:
        form = StudentSelfRegisterForm()
        
    return render(request, "app/general/self_register.html", {"form": form})


def login_view(request):
    """Login user from auth_user table"""
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome {user.username}!")
            
            # Redirect based on user type
            if user.is_staff:
                return redirect('dashboard')  # Staff goes to dashboard
            else:
                return redirect('send_outing_request')  # Students go to outing request
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "app/general/login.html")
    
    return render(request, "app/general/login.html")


@login_required
def log_out(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("index")


# -------------------------
# DASHBOARD (CHECK IN / OUT)
# -------------------------

@login_required
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

                CheckLog.objects.create(
                    student=student,
                    check_out_time=get_current_datetime()
                )

                broadcast_dashboard_update()
                messages.success(request, f"{student.name} checked out successfully.")

            elif student.presence_status == "Out":
                check_in_time = get_current_datetime()
                log = record_check_in(student, check_in_time)

                broadcast_dashboard_update()

                if log.is_late:
                    limit = get_checkin_limit_for_datetime(check_in_time)
                    messages.warning(
                        request,
                        f"Late check-in notice: {student.name} returned after the {limit.strftime('%I:%M %p')} limit."
                    )
                else:
                    messages.success(request, f"{student.name} checked in successfully.")

        except Student.DoesNotExist:
            messages.error(request, "Student not found.")

        return redirect("dashboard")

    # ==========================================
    # GET REQUEST: DATE PARSING & FILTER LOGIC
    # ==========================================
    date_str = request.GET.get('date')
    today = timezone.localdate()
    
    selected_date = today
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today

    # Calculate dates for controls
    prev_date_str = (selected_date - timedelta(days=1)).strftime("%Y-%m-%d")
    next_date_str = (selected_date + timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    selected_date_str = selected_date.strftime("%Y-%m-%d")
    is_today = (selected_date == today)

    # Calculate timezone-aware start and end datetimes for the selected local day
    start_datetime = timezone.make_aware(datetime.combine(selected_date, time.min))
    end_datetime = timezone.make_aware(datetime.combine(selected_date, time.max))

    # ⚡ OPTIMIZATION 1: Fetch check logs along with student data in 1 single query
    logs = CheckLog.objects.filter(
        Q(check_out_time__range=(start_datetime, end_datetime)) |
        Q(check_in_time__range=(start_datetime, end_datetime))
    ).select_related('student')

    # ⚡ OPTIMIZATION 2: Get all active approved outings in ONE query instead of inside a loop
    student_ids = [log.student_id for log in logs]
    approved_outings = OutingRequest.objects.filter(
        student_id__in=student_ids,
        status="Approved"
    ).order_by('request_time')
    
    # Map student IDs to their last approved request for instant memory lookup
    outing_map = {outing.student_id: outing.status for outing in approved_outings}

    log_entries = []
    for log in logs:
        student = log.student
        
        # ⚡ OPTIMIZATION 3: Instant dictionary lookup replaces the slow database loop hit
        request_status = outing_map.get(student.id, "None")

        log_entries.append({
            'student': student,
            'log': log,
            'request_status': request_status,
            'is_late': bool(log.is_late),
        })

    # Sort log entries newest first based on activity times
    log_entries.sort(key=lambda item: (
        item['log'].check_out_time or item['log'].check_in_time or timezone.now(),
        item['log'].check_in_time or item['log'].check_out_time or timezone.now(),
    ), reverse=True)

    return render(request, "app/general/dashboard.html", {
        "log_entries": log_entries,
        "selected_date_str": selected_date_str,
        "prev_date_str": prev_date_str,
        "next_date_str": next_date_str,
        "today_str": today_str,
        "is_today": is_today,
    })


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
        form = StudentForm(request.POST)
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
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student updated successfully.")
            return redirect("manage_students")
    else:
        form = StudentForm(instance=student)
    
    return render(request, "app/general/edit_student.html", {"form": form, "student": student})


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
    students = Student.objects.select_related('user').all().order_by('name')
    return render(request, "app/general/manage_students.html", {"students": students})

# -------------------------
# OUTING REQUESTS (STUDENT ONLY)
# -------------------------

@login_required
def send_outing_request(request):
    """Student submits outing request"""
    
    if request.method == "POST":
        student_id = request.POST.get('student_id')
        destination = request.POST.get('destination')
        reason = request.POST.get('reason')
        outing_date = request.POST.get('outing_date')
        outing_time = request.POST.get('outing_time')
        
        try:
            student = Student.objects.get(student_id=student_id)
            
            OutingRequest.objects.create(
                student=student,
                destination=destination,
                reason=reason,
                outing_date=outing_date,
                outing_time=outing_time,
                status="Pending"
            )
            
            messages.success(request, "Outing request submitted successfully!")
            return redirect('send_outing_request')
            
        except Student.DoesNotExist:
            messages.error(request, "Student not found.")
            return redirect('send_outing_request')
    
    return render(request, "student/outing_request.html")


@login_required
@user_passes_test(lambda u: u.is_staff)
def manage_outing_requests(request):
    """Manage outing requests with bulk actions"""
    
    if request.method == "POST":
        action = request.POST.get("action")
        request_ids = request.POST.getlist("request_ids")
        
        if not request_ids:
            messages.error(request, "Please select at least one request.")
            return redirect("manage_requests")
        
        requests_to_update = OutingRequest.objects.filter(id__in=request_ids)
        
        if action == "approve":
            for req in requests_to_update:
                req.status = "Approved"
                req.student.status = "Approved"
                req.save()
                req.student.save()
            messages.success(request, f"{len(request_ids)} request(s) approved.")
            
        elif action == "reject":
            for req in requests_to_update:
                req.status = "Rejected"
                req.student.status = "Rejected"
                req.save()
                req.student.save()
            messages.success(request, f"{len(request_ids)} request(s) rejected.")
        
        return redirect("manage_requests")
    
    # Show only pending requests
    requests = OutingRequest.objects.filter(status="Pending").order_by("-request_time")
    
    return render(request, "app/general/manage_requests.html", {"requests": requests})


@login_required
@user_passes_test(lambda u: u.is_staff)
def approve_request(request, pk):
    """Approve a single request"""
    req = get_object_or_404(OutingRequest, id=pk)
    req.status = "Approved"
    req.student.status = "Approved"
    req.save()
    req.student.save()

    messages.success(request, f"Request from {req.student.name} approved.")
    return redirect("manage_requests")


@login_required
@user_passes_test(lambda u: u.is_staff)
def reject_request(request, pk):
    """Reject a single request with a mandatory text reasoning input justification"""
    # 💡 FIX: Removed the accidental text tracker here:
    req = get_object_or_404(OutingRequest, id=pk)
    
    if request.method == "POST":
        justification = request.POST.get("justification", "").strip()
        
        if not justification:
            messages.error(request, "You must provide a justification text to reject this request.")
            return redirect("manage_requests")
            
        req.status = "Rejected"
        req.student.status = "Rejected"
        req.save()
        req.student.save()

        messages.info(request, f"Request from {req.student.name} rejected. Reason: {justification}")
    
    return redirect("manage_requests")


@login_required
@user_passes_test(lambda u: u.is_staff)
def view_request(request, pk):
    """View request details"""
    req = get_object_or_404(OutingRequest, id=pk)
    return render(request, "app/general/view_request.html", {"request": req})


@require_http_methods(["GET"])
def get_student_by_id(request, student_id):
    """API endpoint to fetch student details"""
    try:
        student = Student.objects.get(student_id=student_id)
        return JsonResponse({
            'id': student.id,
            'name': student.name,
            'course': student.course,
            'session': student.session,
        })
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)


@require_http_methods(["GET"])
def server_time(request):
    """Return the current server time for synchronized dashboard display."""
    now = timezone.localtime(timezone.now())
    return JsonResponse({
        'server_time': now.strftime('%Y-%m-%d %H:%M:%S')
    })


@require_http_methods(["GET"])
def dashboard_updates(request):
    """Return a lightweight snapshot so the dashboard can refresh on real changes."""
    students = Student.objects.all()
    snapshot = []
    for student in students:
        latest_log = student.check_logs.order_by('-check_in_time', '-check_out_time').first()
        snapshot.append({
            'id': student.id,
            'presence_status': student.presence_status,
            'last_log_id': latest_log.id if latest_log else None,
            'last_log_updated': latest_log.check_in_time or latest_log.check_out_time if latest_log else None,
        })

    now = timezone.localtime(timezone.now())
    return JsonResponse({
        'snapshot': snapshot,
        'server_time': now.strftime('%Y-%m-%d %H:%M:%S'),
    })


@require_http_methods(["GET"])
def dashboard_events(request):
    """Stream dashboard update events to the browser when records change."""
    def event_stream():
        subscriber = SimpleQueue()
        DASHBOARD_EVENT_SUBSCRIBERS.append(subscriber)
        try:
            while True:
                try:
                    message = subscriber.get(timeout=1)
                except Empty:
                    continue
                yield message
        except GeneratorExit:
            pass
        finally:
            if subscriber in DASHBOARD_EVENT_SUBSCRIBERS:
                DASHBOARD_EVENT_SUBSCRIBERS.remove(subscriber)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response