import logging
import threading

from django.contrib.auth.models import User
from django.core.mail import get_connection, EmailMessage

logger = logging.getLogger(__name__)


def warden_emails():
    """Emails of warden accounts that filled in their profile email and left notifications on.

    A warden is an active staff account that is not the superuser and not a GUARD account
    (same rule the profile page uses for the "Warden" badge).
    """
    users = User.objects.filter(
        is_active=True,
        is_staff=True,
        is_superuser=False,
        staff_profile__email_notifications=True,
    ).exclude(staff_profile__tvetmara_email__isnull=True).exclude(
        staff_profile__tvetmara_email=""
    ).exclude(username__icontains="GUARD").select_related("staff_profile")

    emails = []
    for user in users:
        email = user.staff_profile.tvetmara_email.strip()
        if email and email.lower() not in (e.lower() for e in emails):
            emails.append(email)
    return emails


def _send(subject, body, recipients):
    try:
        connection = get_connection()
        messages = [EmailMessage(subject, body, None, [email], connection=connection) for email in recipients]
        connection.send_messages(messages)
    except Exception:
        logger.exception("Failed to email wardens: %s", subject)


def notify_wardens(subject, body):
    """Email every warden in the background, so a slow or broken SMTP never holds up the page."""
    recipients = warden_emails()
    if not recipients:
        return
    threading.Thread(target=_send, args=(subject, body, recipients), daemon=True).start()