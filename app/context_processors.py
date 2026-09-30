from .models import OutingRequest


def pending_requests(request):
    if request.user.is_authenticated and request.user.is_staff:
        qs = OutingRequest.objects.filter(status="Pending").select_related("student").order_by("-request_time")
        return {
            "pending_request_count": qs.count(),
            "pending_requests_preview": qs[:3],
        }
    return {}