from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import RegisterForm, StudentForm, OutingRequestForm
from .models import Student, CheckLog, OutingRequest


# -------------------------
# AUTH VIEWS
# -------------------------

def index(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    context = {
        "registration_form": RegisterForm(),
        "login_form": AuthenticationForm(),
    }

    return render(request, "app/general/index.html", context)


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Registration failed.")

    return redirect("index")


def log_in(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password.")

    return redirect("index")


@login_required
def log_out(request):
    logout(request)
    return redirect("index")


# -------------------------
# DASHBOARD (CHECK IN / OUT)
# -------------------------

@login_required
def dashboard(request):

    if request.method == "POST":
        student_id = request.POST.get("student_id")

        try:
            student = Student.objects.get(student_id=student_id)

            # Block banned
            if student.status == "Banned":
                messages.error(request, "Student is banned.")
                return redirect("dashboard")

            # 🔥 CHECK APPROVAL FROM REQUEST (NOT STUDENT)
            approved_request = OutingRequest.objects.filter(
                student=student,
                status="Approved"
            ).last()

            # CHECK OUT
            if student.presence_status == "In" and approved_request:

                student.presence_status = "Out"
                student.save()

                CheckLog.objects.create(
                    student=student,
                    check_out_time=timezone.now()
                )

                # 🔥 CONSUME THE APPROVAL
                approved_request.status = "Used"
                approved_request.save()

                messages.success(request, "Check-out successful.")

            # CHECK IN
            elif student.presence_status == "Out":
                student.presence_status = "In"
                student.status = "None"  # Reset approval status
                student.save()

                log = student.check_logs.filter(
                    check_in_time__isnull=True
                ).last()

                if log:
                    log.check_in_time = timezone.now()
                    log.save()

                messages.success(request, "Check-in successful.")

            else:
                messages.error(request, "No approved outing request.")

        except Student.DoesNotExist:
            messages.error(request, "Student not found.")

        return redirect("dashboard")

    # Build student data with outing request status
    students = Student.objects.all()
    student_data = []
    
    for student in students:
        # Only show approved requests (not used/rejected)
        latest_request = OutingRequest.objects.filter(
            student=student,
            status="Approved"
        ).last()
        request_status = latest_request.status if latest_request else "None"
        
        student_data.append({
            'student': student,
            'request_status': request_status
        })
    
    return render(request, "app/general/dashboard.html", {"student_data": student_data})


# -------------------------
# CRUD (STAFF ONLY)
# -------------------------

def is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = StudentForm()

    return render(request, "app/general/add_student.html", {"form": form})


@login_required
@user_passes_test(is_staff)
def edit_student(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = StudentForm(instance=student)

    return render(request, "app/general/edit_student.html", {"form": form})


@login_required
@user_passes_test(is_staff)
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        student.delete()
        return redirect("dashboard")

    return render(request, "app/general/delete_student.html", {
        "student": student
    })

# -------------------------
# OUTING REQUESTS (STUDENT ONLY)
# -------------------------

@login_required
def send_outing_request(request):

    if request.method == "POST":
        student_id = request.POST.get("student_id")

        try:
            student = Student.objects.get(student_id=student_id)
        except Student.DoesNotExist:
            messages.error(request, "Student not found.")
            return redirect("send_outing_request")

        form = OutingRequestForm(request.POST)

        if form.is_valid():

            # Prevent duplicate pending request
            existing = OutingRequest.objects.filter(
                student=student,
                status="Pending"
            ).exists()

            if existing:
                messages.error(request, "You already have a pending request.")
                return redirect("send_outing_request")

            outing = form.save(commit=False)
            outing.student = student
            outing.save()

            messages.success(request, "Request submitted.")
            return redirect("dashboard")

    else:
        form = OutingRequestForm()

    return render(request, "student/outing_request.html", {"form": form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def manage_outing_requests(request):

    requests = OutingRequest.objects.all().order_by("-request_time")

    return render(request, "admin/outing_requests.html", {
        "requests": requests
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def approve_request(request, pk):
    req = get_object_or_404(OutingRequest, id=pk)

    req.status = "Approved"
    req.student.status = "Approved"
    req.save()
    req.student.save()

    messages.success(request, "Request approved.")
    return redirect("manage_requests")

@login_required
@user_passes_test(lambda u: u.is_staff)
def reject_request(request, pk):

    req = get_object_or_404(OutingRequest, id=pk)

    req.status = "Rejected"
    req.student.status = "Rejected"
    req.save()
    req.student.save()

    messages.info(request, "Request rejected.")
    return redirect("manage_requests")

@require_http_methods(["GET"])
def get_student_by_id(request, student_id):
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