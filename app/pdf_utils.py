"""PDF letters emailed by ASRAMAku: outing decisions, late-return warnings and bans.

Every public builder returns a BytesIO positioned at 0, ready for
``EmailMessage.attach(name, buffer.getvalue(), "application/pdf")``.
"""
import datetime
import io
import logging
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
    KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

logger = logging.getLogger(__name__)

# Brand colours (same as style.css)
NAVY = colors.HexColor("#0d2f5d")
RED = colors.HexColor("#e73939")
SOFT_TEXT = colors.HexColor("#5f6c7b")
STROKE = colors.HexColor("#e7edf5")
BLUE_SOFT = colors.HexColor("#eaf3ff")

THEMES = {
    "approved": {"accent": colors.HexColor("#1dbf73"), "soft": colors.HexColor("#eafaf3"), "text": colors.HexColor("#0a7d50")},
    "rejected": {"accent": colors.HexColor("#e74c3c"), "soft": colors.HexColor("#fff1f0"), "text": colors.HexColor("#a93a2d")},
    "warning": {"accent": colors.HexColor("#f39c12"), "soft": colors.HexColor("#fff7e8"), "text": colors.HexColor("#9d6802")},
    "ban": {"accent": RED, "soft": colors.HexColor("#fff1f0"), "text": NAVY},
}

PAGE_W, PAGE_H = A4
MARGIN_X = 22 * mm
HEADER_H = 32 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X
LABEL_W = 46 * mm
LOGO_PATH = Path(__file__).resolve().parent / "static" / "app" / "img" / "asramaku_logo_wide.png"
TAGLINE = "Hostel Outing Management System  |  TVETMARA Sungai Petani"

_base = getSampleStyleSheet()
STYLES = {
    "heading": ParagraphStyle("H", parent=_base["Heading2"], fontSize=11.5, leading=14, textColor=NAVY, spaceBefore=12, spaceAfter=5),
    "body": ParagraphStyle("B", parent=_base["Normal"], fontSize=10.5, leading=16),
    "cell": ParagraphStyle("C", parent=_base["Normal"], fontSize=10, leading=14),
    "label": ParagraphStyle("L", parent=_base["Normal"], fontSize=9, leading=13, fontName="Helvetica-Bold"),
    "small": ParagraphStyle("S", parent=_base["Normal"], fontSize=9, leading=13, textColor=SOFT_TEXT),
    "banner": ParagraphStyle("Ban", parent=_base["Normal"], fontSize=14, leading=18, fontName="Helvetica-Bold"),
    "badge": ParagraphStyle("Badge", parent=_base["Normal"], fontSize=9, leading=11, fontName="Helvetica-Bold",
                            textColor=colors.white, alignment=1),
}


# ---------------------------------------------------------------- formatting

def _safe(value, empty="-"):
    """Escape user-entered text so ReportLab doesn't treat it as markup; keep line breaks."""
    text = str(value).strip() if value is not None else ""
    if not text:
        return escape(empty)
    return "<br/>".join(escape(line) for line in text.splitlines())


def _hex(color):
    return "#" + color.hexval()[2:]


def _local(value):
    """Aware datetimes -> Malaysia local time (DB values are stored in UTC)."""
    if isinstance(value, datetime.datetime) and timezone.is_aware(value):
        return timezone.localtime(value)
    return value


def _fmt_time(value):
    return value.strftime("%I:%M %p").lstrip("0")  # 9:05 PM, portable (no %-I on Windows)


def _fmt_date(value):
    return f"{value.day} {value:%B %Y}"


def _fmt_dt(value, empty="-"):
    if not value:
        return empty
    value = _local(value)
    if isinstance(value, datetime.datetime):
        return f"{_fmt_date(value)}, {_fmt_time(value)}"
    if isinstance(value, datetime.date):
        return _fmt_date(value)
    return _fmt_time(value)


def _plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def _duration(delta):
    """timedelta -> '2 days 3 hours 5 minutes' (largest units only, never empty)."""
    minutes = max(int(delta.total_seconds() // 60), 0)
    days, minutes = divmod(minutes, 24 * 60)
    hours, minutes = divmod(minutes, 60)
    parts = [_plural(n, w) for n, w in ((days, "day"), (hours, "hour"), (minutes, "minute")) if n]
    return " ".join(parts) or "less than a minute"


def _person(user, fallback="Hostel warden"):
    if not user:
        return fallback
    return user.get_full_name() or user.username


# ---------------------------------------------------------------- flowables

def _p(text, style="body"):
    return Paragraph(text, STYLES[style])


def _greeting(student):
    return _p(f"Dear <b>{_safe((student.name or '').title(), 'Student')}</b>,")


def _banner(title, subtitle, theme, badge=None):
    """Coloured notice box with an optional status pill on the right."""
    t = THEMES[theme]
    text = [
        Paragraph(f'<font color="{_hex(t["text"])}">{escape(title)}</font>', STYLES["banner"]),
        Spacer(1, 2),
        Paragraph(escape(subtitle), STYLES["small"]),
    ]
    if not badge:
        table = Table([[text]], colWidths=[CONTENT_W])
    else:
        pill = Table([[Paragraph(escape(badge), STYLES["badge"])]], colWidths=[30 * mm])
        pill.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), t["accent"]),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        table = Table([[text, pill]], colWidths=[CONTENT_W - 36 * mm, 36 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), t["soft"]),
        ("LINEBEFORE", (0, 0), (0, -1), 4, t["accent"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("LEFTPADDING", (0, 0), (0, -1), 14),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 12),
    ]))
    return table


def _info_table(rows, label_bg=BLUE_SOFT, label_color=NAVY):
    """Two-column label/value table. Values are escaped here, labels are trusted text."""
    label_style = ParagraphStyle("Lc", parent=STYLES["label"], textColor=label_color)
    data = [[Paragraph(escape(label), label_style), _p(_safe(value), "cell")] for label, value in rows]
    table = Table(data, colWidths=[LABEL_W, CONTENT_W - LABEL_W])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), label_bg),
        ("BOX", (0, 0), (-1, -1), 0.75, STROKE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, STROKE),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ]))
    return table


def _section(title, *flowables):
    """Heading kept on the same page as the block under it."""
    return KeepTogether([_p(escape(title), "heading"), *flowables])


def _numbered(items):
    """Real numbered list with a hanging indent (wrapped lines line up under the text)."""
    return ListFlowable(
        [ListItem(_p(item), leftIndent=16, value=i) for i, item in enumerate(items, start=1)],
        bulletType="1", bulletFormat="%s.", bulletFontSize=10.5, bulletColor=NAVY,
        bulletFontName="Helvetica-Bold", leftIndent=16, spaceBefore=2,
    )


def _student_rows(student):
    return [
        ("Name", student.name),
        ("Matric ID", student.student_id),
        ("Course", student.course),
        ("Session", student.session),
    ]


def _sign_off():
    return KeepTogether([
        Spacer(1, 14),
        _p("Thank you.<br/><br/><b>Hostel Warden</b><br/>TVETMARA Sungai Petani"),
        _p("Sent via ASRAMAku", "small"),
    ])


# ---------------------------------------------------------------- page chrome

@lru_cache(maxsize=1)
def _logo():
    """Logo image reader, or None if the file is missing/unreadable (text wordmark is used instead)."""
    try:
        return ImageReader(str(LOGO_PATH))
    except Exception:
        logger.warning("PDF logo not found or unreadable at %s; using text wordmark", LOGO_PATH)
        return None


def _draw_wordmark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 22)
    canvas.setFillColor(NAVY)
    canvas.drawString(x, y, "ASRAMA")
    canvas.setFillColor(RED)
    canvas.drawString(x + canvas.stringWidth("ASRAMA", "Helvetica-Bold", 22), y, "ku")


class _NumberedCanvas(rl_canvas.Canvas):
    """Holds pages until save() so the footer can say 'Page X of Y'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_pages)
        for state in self._saved_pages:
            self.__dict__.update(state)
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(SOFT_TEXT)
            self.drawRightString(PAGE_W - MARGIN_X, 12 * mm, f"Page {self._pageNumber} of {total}")
            self.restoreState()
            super().showPage()
        super().save()


def _letterhead(canvas, doc):
    """White header with logo, navy/red rule and footer, drawn on every page."""
    canvas.saveState()
    top = PAGE_H - 10 * mm

    logo = _logo()
    if logo:
        img_w, img_h = logo.getSize()
        h = 13 * mm
        canvas.drawImage(logo, MARGIN_X, top - h, width=h * img_w / img_h, height=h, mask="auto")
    else:
        _draw_wordmark(canvas, MARGIN_X, top - 10 * mm)
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(SOFT_TEXT)
    canvas.drawString(MARGIN_X, top - 18.5 * mm, TAGLINE)

    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(PAGE_W - MARGIN_X, top - 3 * mm, "REFERENCE NO.")
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(NAVY)
    canvas.drawRightString(PAGE_W - MARGIN_X, top - 8 * mm, doc.ref_no)
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(SOFT_TEXT)
    canvas.drawRightString(PAGE_W - MARGIN_X, top - 13 * mm, doc.issued_on)

    rule_y = PAGE_H - HEADER_H
    canvas.setFillColor(NAVY)
    canvas.rect(0, rule_y, PAGE_W, 1.6 * mm, stroke=0, fill=1)
    canvas.setFillColor(RED)
    canvas.rect(0, rule_y - 0.8 * mm, PAGE_W, 0.8 * mm, stroke=0, fill=1)

    canvas.setStrokeColor(STROKE)
    canvas.setLineWidth(0.75)
    canvas.line(MARGIN_X, 18 * mm, PAGE_W - MARGIN_X, 18 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SOFT_TEXT)
    canvas.drawString(MARGIN_X, 12 * mm, f"{doc.ref_no}  |  Computer-generated letter, no signature required.")
    canvas.restoreState()


def _build(story, ref_no, now, subject):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=HEADER_H + 7 * mm, bottomMargin=24 * mm,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        title=f"{subject} ({ref_no})", author="ASRAMAku", subject=subject,
        creator="ASRAMAku Hostel Outing Management System",
    )
    doc.ref_no = ref_no
    doc.issued_on = f"Issued {_fmt_dt(now)}"
    doc.build(story, onFirstPage=_letterhead, onLaterPages=_letterhead, canvasmaker=_NumberedCanvas)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------- letters

def build_decision_letter_pdf(req, now, justification=""):
    """Approval or rejection letter for an outing request. Returns a BytesIO."""
    approved = req.status == "Approved"
    theme = "approved" if approved else "rejected"
    student = req.student
    ref_no = f"ASR/OUT/{req.id:05d}"
    home_leave = req.request_type == "Home Leave"
    outing_when = " ".join(filter(None, [
        _fmt_date(req.outing_date) if req.outing_date else "",
        _fmt_time(req.outing_time) if req.outing_time else "",
    ]))
    kind = "home leave" if home_leave else "outing"

    story = [
        _greeting(student),
        Spacer(1, 8),
        _banner(
            f"{kind.upper()} REQUEST {'APPROVED' if approved else 'REJECTED'}",
            f"Request submitted on {_fmt_dt(req.request_time)}",
            theme,
            badge=req.status.upper(),
        ),
        Spacer(1, 8),
        _p(
            f"Your {kind} request has been reviewed and <b>approved</b> by the hostel warden. "
            "Please follow the conditions listed below."
            if approved else
            f"Your {kind} request has been reviewed and <b>rejected</b> by the hostel warden. "
            "The reason given is stated below."
        ),
        _section("Student Details", _info_table(_student_rows(student))),
        _section("Request Details", _info_table([
            ("Type", req.request_type),
            ("Destination", req.destination),
            ("Purpose", req.reason),
            ("Outing date / time", outing_when),
            ("Return by", f"{_fmt_date(req.return_date)}, by curfew" if req.return_date else "Same day, by curfew"),
            ("Decision", req.status),
        ])),
    ]

    if approved:
        story.append(_section("Conditions", _numbered([
            "Scan your ID card / RFID at the hostel entrance when leaving and returning.",
            "Return before the hostel curfew. Late returns are recorded and a warning letter is issued automatically.",
            "Keep this letter as proof of approval until you have checked back in.",
        ])))
    else:
        t = THEMES["rejected"]
        story += [
            _section("Warden's Justification", _info_table(
                [("Reason", justification or "No reason was given. Please contact the hostel warden.")],
                label_bg=t["soft"], label_color=t["text"],
            )),
            Spacer(1, 10),
            _p("You may submit a new request after addressing the reason above. "
               "Please contact the hostel warden if you need clarification."),
        ]

    story.append(_sign_off())
    return _build(story, ref_no, now, f"{kind.capitalize()} request {req.status.lower()}")


def build_warning_letter_pdf(student, out_time, deadline, now):
    """Late-return warning letter. Returns a BytesIO. (Same signature as before.)"""
    now, out_time, deadline = _local(now), _local(out_time), _local(deadline)
    ref_no = f"ASR/WRN/{student.student_id}/{now:%Y%m%d%H%M}"
    t = THEMES["warning"]

    story = [
        _greeting(student),
        Spacer(1, 8),
        _banner("LATE RETURN WARNING", "Official notice: return deadline exceeded", "warning", badge="OVERDUE"),
        Spacer(1, 8),
        _p("Our records show that you have <b>not returned to the hostel</b> by the required curfew time. "
           "This letter serves as an official warning and a copy has been sent to the hostel warden."),
        _section("Student Details", _info_table(_student_rows(student))),
        _section("Outing Record", _info_table([
            ("Checked out", _fmt_dt(out_time)),
            ("Return deadline", _fmt_dt(deadline)),
            ("Overdue by", f"{_duration(now - deadline)} (as of {_fmt_time(now)})"),
            ("Status", "Not yet checked in"),
        ], label_bg=t["soft"], label_color=t["text"])),
        _section("Action Required", _numbered([
            "Return to the hostel immediately and scan your ID card / RFID at the entrance.",
            "Report to the hostel warden upon arrival.",
        ])),
        Spacer(1, 6),
        _p("Repeated late returns may result in further disciplinary action in accordance with hostel regulations.", "small"),
        _sign_off(),
    ]
    return _build(story, ref_no, now, "Late return warning")


def build_ban_letter_pdf(ban, now):
    """Ban letter for a student. Returns a BytesIO."""
    student = ban.student
    ref_no = f"ASR/BAN/{ban.id:05d}"
    t = THEMES["ban"]
    starts = _local(ban.starts_at)
    ends = _local(ban.ends_at)

    rows = [
        ("Reason", ban.reason),
        ("Ban starts", _fmt_dt(starts)),
        ("Ban ends", _fmt_dt(ends) if ends else "Until lifted by the warden"),
    ]
    if ends and starts and ends > starts:
        rows.append(("Duration", _duration(ends - starts)))
    rows.append(("Issued by", _person(ban.banned_by)))

    story = [
        _greeting(student),
        Spacer(1, 8),
        _banner("OUTING BAN NOTICE", "Official notice: outing and home leave privileges suspended", "ban", badge="BANNED"),
        Spacer(1, 8),
        _p("The hostel warden has <b>banned</b> you from leaving the hostel for the period stated below. "
           "During this period you cannot check out at the hostel entrance or submit a home leave request."),
        _section("Student Details", _info_table(_student_rows(student))),
        _section("Ban Details", _info_table(rows, label_bg=t["soft"], label_color=t["text"])),
        _section("Please Note", _numbered([
            "Your privileges return automatically when the ban ends. No action is needed from you."
            if ends else
            "Your privileges return when the warden lifts the ban. You will be able to check out again after that.",
            "If you are outside the hostel now, you can still scan back in as usual.",
            "Contact the hostel warden if you believe this ban was issued in error.",
        ])),
        _sign_off(),
    ]
    return _build(story, ref_no, now, "Outing ban notice")