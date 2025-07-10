from reportlab.lib.pagesizes import legal, letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile
import os

# Add your PDF generation functions here. Example:
def generate_invoice_pdf(data, filename):

    c = canvas.Canvas(filename, pagesize=legal)
    width, height = legal

    # --- Modern Header Bar ---
    header_color = colors.HexColor("#2D3E50")
    c.setFillColor(header_color)
    c.rect(0, height - 1.1 * inch, width, 1.1 * inch, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(1 * inch, height - 0.65 * inch, data.get("header", "BILLING STATEMENT"))
    # Logo placeholder (optional):
    # c.drawImage('logo.png', width - 2*inch, height - 1*inch, width=1*inch, height=1*inch, mask='auto')

    # --- Company/Contact Info ---
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#222222"))
    c.drawString(1 * inch, height - 1.35 * inch, data.get("receiver", ""))
    if data.get("position"):
        c.drawString(1 * inch, height - 1.55 * inch, data["position"])
    if data.get("company_contact"):
        c.drawString(1 * inch, height - 1.75 * inch, data["company_contact"])

    # --- Invoice Details (right side) ---
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.white)
    c.drawRightString(width - 1 * inch, height - 0.65 * inch, f"Date: {data.get('date', '')}")
    c.drawRightString(width - 1 * inch, height - 0.95 * inch, f"Status: {data.get('status', '').upper()}")

    # --- Client Info ---
    y = height - 2.2 * inch
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#2D3E50"))
    c.drawString(1 * inch, y, "Bill To:")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#222222"))
    c.drawString(1 * inch, y - 0.2 * inch, data.get("client_name", ""))

    # --- Service Description ---
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#2D3E50"))
    c.drawString(1 * inch, y - 0.5 * inch, "Service:")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#222222"))
    c.drawString(1 * inch, y - 0.7 * inch, data.get("service", ""))

    # --- Body Message (if any) ---
    if data.get("body_message"):
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import Frame
        body_style = ParagraphStyle(
            'Body', fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#444444"), spaceAfter=8
        )
        body = Paragraph(data["body_message"].replace("\n", "<br/>"), body_style)
        body_frame = Frame(1 * inch, y - 2.1 * inch, width - 2 * inch, 0.7 * inch, showBoundary=0)
        body_frame.addFromList([body], c)

    # --- Items Table ---
    table_data = [["Description", "Qty", "Unit Price", "Amount"]]
    for item in data.get("items", []):
        try:
            qty_val = float(item.get("qty") or 0)
            amount_val = float(item.get("amount") or 0)
            total = qty_val * amount_val
            table_data.append([
                item.get("description", ""),
                item.get("qty", ""),
                f"PHP {amount_val:,.2f}",
                f"PHP {total:,.2f}"
            ])
        except ValueError:
            pass

    # Add subtotal row
    subtotal = data.get("subtotal", "PHP 0.00")
    table_data.append(["", "", "Subtotal:", subtotal])

    table = Table(table_data, colWidths=[3.5*inch, 0.8*inch, 1*inch, 1.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4B8DF8")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (2, 1), (3, -1), 'RIGHT'),  # Ensure right alignment for currency columns
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -2), colors.HexColor("#222222")),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E0E0E0")),
        ('FONTNAME', (0, -1), (-2, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-2, -1), colors.HexColor("#F5F5F5")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#2D3E50")),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor("#4B8DF8")),
    ]))
    table.wrapOn(c, width, height)
    table.drawOn(c, 1 * inch, y - 2.5 * inch)

    # --- Attorney (Prepared by) ---
    if data.get("attorney"):
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#2D3E50"))
        c.drawString(1 * inch, 0.85 * inch, f"Prepared by: {data['attorney']}")

    # --- Footer ---
    c.setStrokeColor(colors.HexColor("#E0E0E0"))
    c.setLineWidth(0.5)
    c.line(0.5 * inch, 0.7 * inch, width - 0.5 * inch, 0.7 * inch)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#888888"))
    footer_text = data.get("footer", "Thank you for your business!")
    c.drawCentredString(width / 2, 0.5 * inch, footer_text)

    c.save()
