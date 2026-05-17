from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
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
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Registration failed.")

    return redirect("index")


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
                messages.error(request, "Student is already In. No approved outing request to check out.")

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
    """View all students and manage them"""
    students = Student.objects.all().order_by('name')
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
    """Reject a single request"""
    req = get_object_or_404(OutingRequest, id=pk)
    req.status = "Rejected"
    req.student.status = "Rejected"
    req.save()
    req.student.save()

    messages.info(request, f"Request from {req.student.name} rejected.")
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