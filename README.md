# ASRAMAku

**Web-based hostel outing management system** for TVETMARA Sungai Petani, built with Django and designed to run on a Raspberry Pi with RFID check-in/out.

Final Year Project, Diploma in Applied Electronics Engineering Technology (DFK40392).

---

## Features

- **RFID / ID check-in and check-out:** students scan their card at the hostel entrance; the dashboard updates in real time.
- **Curfew tracking:** automatic late detection (7:00 PM Sun–Wed, 10:00 PM Thu–Sat, or a manual override set by staff).
- **Home leave permits:** students apply online with a return date; wardens approve or reject with a justification. Outings need no permit.
- **Email notifications:** students receive an email with an official **PDF letter** when a request is approved or rejected.
- **Automated late-return warnings:** a scheduled command emails a **PDF warning letter** to the student and warden when a student is overdue.
- **Notification bell:** wardens see the pending request count and the latest requests from any page.
- **Student management:** add, edit and delete student records, including RFID UID and profile photo.
- **PWA support:** installable on mobile and desktop.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Django 6 |
| Database | MySQL |
| Frontend | Bootstrap 5, Font Awesome, vanilla JavaScript |
| PDF generation | ReportLab |
| Email | SMTP (Gmail App Password) |
| Hardware | Raspberry Pi, RFID reader |

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/biscuitCurry/ASRAMAku.git
cd ASRAMAku
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / Raspberry Pi
pip install -r requirements.txt
```

### 2. Create the database

Create a MySQL database named `hostel_pwa_db`.

### 3. Configure environment variables

Create a `.env` file in the project root (next to `manage.py`):

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DB_PASSWORD=your-mysql-password

EMAIL_HOST_USER=youraccount@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
WARDEN_EMAIL=warden@example.com
```

> `.env` is git-ignored. Never commit real credentials.

### 4. Migrate and run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

On Windows you can also double-click `runserver.bat`.

Open http://127.0.0.1:8000/ and log in with a staff account.

## Late-Return Warnings

Overdue students are detected by a management command:

```bash
python manage.py check_overdue --dry-run   # list overdue students only
python manage.py check_overdue             # send warning emails with PDF
```

Each late return is warned once. In production, schedule it with cron, e.g. every 15 minutes:

```cron
*/15 * * * * cd /path/to/ASRAMAku && .venv/bin/python manage.py check_overdue
```

##
