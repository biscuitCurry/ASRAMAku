import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import CheckLog, OutingTimeSettings
from app.pdf_utils import build_warning_letter_pdf


class Command(BaseCommand):
    help = "Email a PDF warning letter to the student and warden for late returns."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        now = timezone.localtime(timezone.now())
        cfg, _ = OutingTimeSettings.objects.get_or_create(pk=1)

        open_logs = CheckLog.objects.filter(
            check_out_time__isnull=False,
            check_in_time__isnull=True,
            warning_sent=False,
            student__presence_status="Out",
        ).select_related("student")

        count = 0
        for log in open_logs:
            out_time = timezone.localtime(log.check_out_time)
            curfew = cfg.get_active_curfew_time(out_time)
            deadline = timezone.make_aware(datetime.datetime.combine(out_time.date(), curfew))
            if out_time.time() >= curfew:
                deadline += datetime.timedelta(days=1)
            if now <= deadline:
                continue

            student = log.student
            self.stdout.write(f"OVERDUE: {student.name} (out {out_time:%d %b %H:%M}, due {deadline:%d %b %H:%M})")
            count += 1
            if options["dry_run"]:
                continue

            pdf_buffer = build_warning_letter_pdf(student, out_time, deadline, now)
            filename = f"warning_{student.student_id}_{now:%Y%m%d%H%M}.pdf"

            recipients = [e for e in [student.tvetmara_email, settings.WARDEN_EMAIL] if e]
            sent_any = False
            if recipients:
                try:
                    msg = EmailMessage(
                        subject=f"Late Return Warning — {student.name}",
                        body=f"A late-return warning letter for {student.name} ({student.student_id}) is attached.",
                        from_email=None,
                        to=recipients,
                    )
                    msg.attach(filename, pdf_buffer.getvalue(), "application/pdf")
                    msg.send()
                    sent_any = True
                except Exception as exc:
                    self.stderr.write(f"Email failed: {exc}")

            if sent_any:
                log.warning_sent = True
                log.save(update_fields=["warning_sent"])

        self.stdout.write(self.style.SUCCESS(f"Done. {count} overdue."))