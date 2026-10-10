
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth


def _draw_centered_text(
    pdf, text, x_center, y, font_name, font_size, max_width
):
    """Draw centered text, reducing the font size if necessary."""
    text = str(text)
    while (
        font_size > 10
        and stringWidth(text, font_name, font_size) > max_width
    ):
        font_size -= 1

    pdf.setFont(font_name, font_size)
    pdf.drawCentredString(x_center, y, text)


def generate_certificate(
    recipient_name: str,
    course_name: str,
    completion_date: str,
    certificate_id: str,
    output_path: str,
) -> str:
    """Generate one PDF certificate and return its file path."""

    # Validate required fields
    fields = {
        "recipient_name": recipient_name,
        "course_name": course_name,
        "completion_date": completion_date,
        "certificate_id": certificate_id,
    }

    for field_name, value in fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")

    # Create the output folder if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Set up an A4 landscape PDF
    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(str(output_file), pagesize=(page_width, page_height))

    center_x = page_width / 2
    gold = colors.HexColor("#B08D36")
    navy = colors.HexColor("#183153")

    # White background and decorative borders
    pdf.setFillColor(colors.white)
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    pdf.setStrokeColor(navy)
    pdf.setLineWidth(4)
    pdf.rect(22, 22, page_width - 44, page_height - 44)

    pdf.setStrokeColor(gold)
    pdf.setLineWidth(1.5)
    pdf.rect(32, 32, page_width - 64, page_height - 64)

    # Main heading
    pdf.setFillColor(gold)
    _draw_centered_text(
        pdf, "CERTIFICATE OF COMPLETION",
        center_x, page_height - 105, "Helvetica-Bold", 27,
        page_width - 100
    )

    # Introductory text
    pdf.setFillColor(navy)
    _draw_centered_text(
        pdf, "This certificate is proudly presented to",
        center_x, page_height - 155, "Helvetica", 14,
        page_width - 100
    )

    # Recipient name
    pdf.setFillColor(colors.black)
    _draw_centered_text(
        pdf, recipient_name.strip(),
        center_x, page_height - 215, "Helvetica-Bold", 30,
        page_width - 100
    )

    # Course details
    pdf.setFillColor(navy)
    _draw_centered_text(
        pdf, "For successfully completing",
        center_x, page_height - 255, "Helvetica", 14,
        page_width - 100
    )

    pdf.setFillColor(gold)
    _draw_centered_text(
        pdf, course_name.strip(),
        center_x, page_height - 295, "Helvetica-Bold", 20,
        page_width - 100
    )

    # Decorative separator
    pdf.setStrokeColor(gold)
    pdf.setLineWidth(1.5)
    pdf.line(100, 105, page_width - 100, 105)

    # Completion date and certificate ID
    pdf.setFillColor(navy)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(80, 78, "COMPLETION DATE")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(80, 60, completion_date.strip())

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(
        page_width - 80, 78, "CERTIFICATE ID"
    )

    pdf.setFont("Helvetica", 11)
    pdf.drawRightString(
        page_width - 80, 60, certificate_id.strip()
    )

    # Finish and save the PDF
    pdf.showPage()
    pdf.save()

    return str(output_file.resolve())
