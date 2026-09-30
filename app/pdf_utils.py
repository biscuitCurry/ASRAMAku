import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def build_warning_letter_pdf(student, out_time, deadline, now):
    """Return a BytesIO containing a structured late-return warning letter."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=25 * mm, bottomMargin=20 * mm,
        leftMargin=22 * mm, rightMargin=22 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("LetterTitle", parent=styles["Title"], fontSize=16, spaceAfter=4)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], textColor=colors.HexColor("#5f6c7b"), spaceAfter=16)
    heading_style = ParagraphStyle("SectionHeading", parent=styles["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5, leading=16)

    story = []

    story.append(Paragraph("ASRAMAku", title_style))
    story.append(Paragraph("Hostel Management System — Late Return Notice", subtitle_style))
    story.append(Paragraph(f"Date issued: {now:%d %B %Y, %I:%M %p}", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Subject: Warning — Late Return from Outing / Home Leave", heading_style))
    story.append(Paragraph(
        f"This letter serves as an official notice that the student named below did not "
        f"return to the hostel by the required curfew time and is recorded as late.",
        body_style,
    ))

    story.append(Paragraph("Student Details", heading_style))
    details = [
        ["Name", student.name],
        ["Matric ID", student.student_id],
        ["Course", student.course],
        ["Session", student.session],
    ]
    table = Table(details, colWidths=[45 * mm, 110 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf3ff")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#0d2f5d")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7edf5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)

    story.append(Paragraph("Outing Record", heading_style))
    record = [
        ["Checked out", f"{out_time:%d %B %Y, %I:%M %p}"],
        ["Return deadline", f"{deadline:%d %B %Y, %I:%M %p}"],
        ["Status at time of notice", "Not yet checked in"],
    ]
    table2 = Table(record, colWidths=[45 * mm, 110 * mm])
    table2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#fff1f0")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#a93a2d")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7edf5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table2)

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "The student is reminded to observe the hostel's curfew policy. Repeated late returns "
        "may result in further disciplinary action in accordance with hostel regulations.",
        body_style,
    ))

    story.append(Spacer(1, 28))
    story.append(Paragraph("Issued automatically by ASRAMAku on behalf of the hostel warden.", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer