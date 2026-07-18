from datetime import datetime, time

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Student
from .views import get_checkin_limit_for_datetime, get_current_datetime, is_late_checkin


class CheckInLimitTests(TestCase):
    def test_weekday_limit_is_7pm(self):
        dt = datetime(2026, 7, 6, 19, 1)  # Monday
        self.assertEqual(get_checkin_limit_for_datetime(dt), time(19, 0))

    def test_sunday_limit_is_7pm(self):
        dt = datetime(2026, 7, 5, 19, 1)  # Sunday
        self.assertEqual(get_checkin_limit_for_datetime(dt), time(19, 0))

    def test_weekend_limit_is_10pm(self):
        dt = datetime(2026, 7, 4, 22, 1)  # Saturday
        self.assertEqual(get_checkin_limit_for_datetime(dt), time(22, 0))

    def test_late_checkin_is_detected_after_limit(self):
        dt = datetime(2026, 7, 6, 19, 1)  # Monday, 7:01 PM
        self.assertTrue(is_late_checkin(dt))

    def test_on_time_checkin_is_not_late(self):
        dt = datetime(2026, 7, 6, 18, 59)  # Monday, 6:59 PM
        self.assertFalse(is_late_checkin(dt))


class CurrentTimeTests(TestCase):
    @override_settings(TIME_ZONE='Asia/Kuala_Lumpur')
    def test_get_current_datetime_uses_configured_timezone(self):
        dt = get_current_datetime()
        self.assertEqual(dt.tzinfo, timezone.get_current_timezone())


class DashboardUpdatesTests(TestCase):
    def test_dashboard_updates_endpoint_returns_snapshot(self):
        Student.objects.create(
            name="Aqil",
            course="CS",
            session="2024/2025",
            student_id="2024006",
            id_card="IC006",
            rfid_uid="RFID006",
            presence_status="In",
        )

        response = self.client.get(reverse("dashboard_updates"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("snapshot", data)
        self.assertIn("server_time", data)

    def test_dashboard_renders_log_history_rows(self):
        user = User.objects.create_user(username="warden", password="secret", is_staff=True)
        student = Student.objects.create(
            name="Aqil",
            course="CS",
            session="2024/2025",
            student_id="2024008",
            id_card="IC008",
            rfid_uid="RFID008",
            presence_status="In",
        )
        self.client.force_login(user)

        self.client.post(reverse("dashboard"), {"student_id": student.student_id})
        self.client.post(reverse("dashboard"), {"student_id": student.student_id})

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("log_entries", response.context)
        self.assertEqual(len(response.context["log_entries"]), 1)
        self.assertIsNotNone(response.context["log_entries"][0]["log"].check_in_time)


class DashboardQuickToggleTests(TestCase):
    def test_dashboard_quick_toggle_uses_student_id(self):
        user = User.objects.create_user(username="warden", password="secret", is_staff=True)
        student = Student.objects.create(
            name="Aqil",
            course="CS",
            session="2024/2025",
            student_id="2024002",
            id_card="IC002",
            rfid_uid="RFID002",
            presence_status="In",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("dashboard"), {"student_id": student.student_id})

        self.assertEqual(response.status_code, 302)
        student.refresh_from_db()
        self.assertEqual(student.presence_status, "Out")

    def test_dashboard_quick_toggle_accepts_id_card(self):
        user = User.objects.create_user(username="warden", password="secret", is_staff=True)
        student = Student.objects.create(
            name="Aqil",
            course="CS",
            session="2024/2025",
            student_id="2024003",
            id_card="IC003",
            rfid_uid="RFID003",
            presence_status="In",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("dashboard"), {"student_id": student.id_card})

        self.assertEqual(response.status_code, 302)
        student.refresh_from_db()
        self.assertEqual(student.presence_status, "Out")

    def test_dashboard_quick_toggle_accepts_whitespace_and_case(self):
        user = User.objects.create_user(username="warden", password="secret", is_staff=True)
        student = Student.objects.create(
            name="Aqil",
            course="CS",
            session="2024/2025",
            student_id="2024004",
            id_card="IC004",
            rfid_uid="RFID004",
            presence_status="In",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("dashboard"), {"student_id": f"  {student.student_id.upper()}  "})

        self.assertEqual(response.status_code, 302)
        student.refresh_from_db()
        self.assertEqual(student.presence_status, "Out")
