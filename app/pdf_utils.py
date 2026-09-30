import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
}

PAGE_W, PAGE_H = A4
_base = getSampleStyleSheet()
STYLES = {
    "heading": ParagraphStyle("H", parent=_base["Heading2"], fontSize=11.5, textColor=NAVY, spaceBefore=14, spaceAfter=6),
    "body": ParagraphStyle("B", parent=_base["Normal"], fontSize=10.5, leading=16),
    "small": ParagraphStyle("S", parent=_base["Normal"], fontSize=9, leading=13, textColor=SOFT_TEXT),
    "banner": ParagraphStyle("Ban", parent=_base["Normal"], fontSize=14, leading=18, fontName="Helvetica-Bold"),
}


def _p(text, style="body"):
    return Paragraph(text, STYLES[style])


def _safe(value):
    """Escape user-entered text so ReportLab doesn't treat it as markup."""
    return escape(str(value or "-"))


def _letterhead(canvas, doc):
    """Navy header band + footer, drawn on every page."""
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 30 * mm, PAGE_W, 30 * mm, stroke=0, fill=1)
    canvas.setFillColor(RED)
    canvas.rect(0, PAGE_H - 31.5 * mm, PAGE_W, 1.5 * mm, stroke=0, fill=1)

    canvas.setFont("Helvetica-Bold", 22)
    canvas.setFillColor(RED)
    canvas.drawString(22 * mm, PAGE_H - 17 * mm, "ASRAMA")
    canvas.setFillColor(colors.white)
    canvas.drawString(22 * mm + canvas.stringWidth("ASRAMA", "Helvetica-Bold", 22), PAGE_H - 17 * mm, "ku")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#c9d6e8"))
    canvas.drawString(22 * mm, PAGE_H - 23.5 * mm, "Hostel Outing Management System  |  TVETMARA Sungai Petani")

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(colors.white)
    canvas.drawRightString(PAGE_W - 22 * mm, PAGE_H - 15 * mm, doc.ref_no)
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#c9d6e8"))
    canvas.drawRightString(PAGE_W - 22 * mm, PAGE_H - 21 * mm, doc.issued_on)

    canvas.setStrokeColor(STROKE)
    canvas.line(22 * mm, 18 * mm, PAGE_W - 22 * mm, 18 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SOFT_TEXT)
    canvas.drawString(22 * mm, 12 * mm, "This letter was generated automatically by ASRAMAku and does not require a signature.")
    canvas.drawRightString(PAGE_W - 22 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _banner(title, subtitle, theme):
    t = THEMES[theme]
    cell = [
        Paragraph(f'<font color="{t["text"].hexval().replace("0x", "#")}">{title}</font>', STYLES["banner"]),
        Paragraph(subtitle, STYLES["small"]),
    ]
    table = Table([[cell]], colWidths=[PAGE_W - 44 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), t["soft"]),
        ("LINEBEFORE", (0, 0), (0, -1), 4, t["accent"]),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return table


def _info_table(rows, label_bg=BLUE_SOFT, label_color=NAVY):
    data = [[_p(f"<b>{label}</b>", "small"), _p(_safe(value))] for label, value in rows]
    table = Table(data, colWidths=[48 * mm, PAGE_W - 44 * mm - 48 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), label_bg),
        ("TEXTCOLOR", (0, 0), (0, -1), label_color),
        ("GRID", (0, 0), (-1, -1), 0.5, STROKE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _student_rows(student):
    return [
        ("Name", student.name),
        ("Matric ID", student.student_id),
        ("Course", student.course),
        ("Session", student.session),
    ]


def _build(story, ref_no, issued_on):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=40 * mm, bottomMargin=24 * mm,
        leftMargin=22 * mm, rightMargin=22 * mm,
        title=ref_no, author="ASRAMAku",
    )
    doc.ref_no = ref_no
    doc.issued_on = issued_on
    doc.build(story, onFirstPage=_letterhead, onLaterPages=_letterhead)
    buffer.seek(0)
    return buffer


def build_decision_letter_pdf(req, now, justification=""):
    """Approval or rejection letter for an outing request. Returns a BytesIO."""
    approved = req.status == "Approved"
    theme = "approved" if approved else "rejected"
    student = req.student
    ref_no = f"ASR/OUT/{req.id:05d}"
    outing_when = " ".join(filter(None, [
        req.outing_date.strftime("%d %B %Y") if req.outing_date else "",
        req.outing_time.strftime("%I:%M %p") if req.outing_time else "",
    ]))

    story = [
        _p(f"Dear <b>{_safe(student.name.title())}</b>,"),
        Spacer(1, 8),
        _banner(
            "OUTING REQUEST APPROVED" if approved else "OUTING REQUEST REJECTED",
            f"Request submitted on {req.request_time:%d %B %Y, %I:%M %p}",
            theme,
        ),
        Spacer(1, 6),
        _p(
            "Your outing request has been reviewed and <b>approved</b> by the hostel warden. "
            "Please follow the conditions listed below."
            if approved else
            "Your outing request has been reviewed and <b>rejected</b> by the hostel warden. "
            "The reason given is stated below."
        ),
        _p("Student Details", "heading"),
        _info_table(_student_rows(student)),
        _p("Request Details", "heading"),
        _info_table([
            ("Destination", req.destination),
            ("Purpose", req.reason),
            ("Type", req.request_type),
            ("Return by", f"{req.return_date:%d %B %Y}, by curfew" if req.return_date else "Same day, by curfew"),
            ("Outing date / time", outing_when),
            ("Decision", req.status),
        ]),
    ]

    if approved:
        story += [
            _p("Conditions", "heading"),
            _p("1. Scan your ID card / RFID at the hostel entrance when leaving and returning."),
            _p("2. Return before the hostel curfew. Late returns are recorded and a warning letter is issued automatically."),
            _p("3. Keep this letter as proof of approval until you have checked back in."),
        ]
    else:
        t = THEMES["rejected"]
        story += [
            _p("Warden's Justification", "heading"),
            _info_table([("Reason", justification)], label_bg=t["soft"], label_color=t["text"]),
            Spacer(1, 10),
            _p("You may submit a new request after addressing the reason above. "
               "Please contact the hostel warden if you need clarification."),
        ]

    return _build(story, ref_no, f"Issued {now:%d %B %Y, %I:%M %p}")


def build_warning_letter_pdf(student, out_time, deadline, now):
    """Late-return warning letter. Returns a BytesIO. (Same signature as before.)"""
    ref_no = f"ASR/WRN/{student.student_id}/{now:%Y%m%d%H%M}"
    overdue = now - deadline
    hours, rem = divmod(int(overdue.total_seconds()), 3600)
    overdue_text = f"{hours} hour(s) {rem // 60} minute(s)"
    t = THEMES["warning"]

    story = [
        _p(f"Dear <b>{_safe(student.name.title())}</b>,"),
        Spacer(1, 8),
        _banner("LATE RETURN WARNING", "Official notice: return deadline exceeded", "warning"),
        Spacer(1, 6),
        _p("Our records show that you have <b>not returned to the hostel</b> by the required curfew time. "
           "This letter serves as an official warning and a copy has been sent to the hostel warden."),
        _p("Student Details", "heading"),
        _info_table(_student_rows(student)),
        _p("Outing Record", "heading"),
        _info_table([
            ("Checked out", f"{out_time:%d %B %Y, %I:%M %p}"),
            ("Return deadline", f"{deadline:%d %B %Y, %I:%M %p}"),
            ("Overdue by", overdue_text),
            ("Status", "Not yet checked in"),
        ], label_bg=t["soft"], label_color=t["text"]),
        _p("Action Required", "heading"),
        _p("1. Return to the hostel immediately and scan your ID card / RFID at the entrance."),
        _p("2. Report to the hostel warden upon arrival."),
        _p("Repeated late returns may result in further disciplinary action in accordance with hostel regulations.", "small"),
    ]
    return _build(story, ref_no, f"Issued {now:%d %B %Y, %I:%M %p}")