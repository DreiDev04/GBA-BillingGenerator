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

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]
    bold_style = ParagraphStyle(
        "Bold",
        parent=normal_style,
        fontName="Helvetica-Bold"
    )

    # Invoice Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "BILLING STATEMENT")

    # Company Info
    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, height - 1.5 * inch, data.get("receiver", ""))
    if data.get("position"):
        c.drawString(1 * inch, height - 1.7 * inch, data["position"])

    # Invoice Details
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 1 * inch, height - 1 * inch, f"Invoice Date: {data.get('date', '')}")
    c.drawRightString(width - 1 * inch, height - 1.2 * inch, f"Status: {data.get('status', '').upper()}")

    # Client Info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 2.2 * inch, "Bill To:")
    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, height - 2.4 * inch, data.get("client_name", ""))

    # Service Description
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 2.8 * inch, "Service:")
    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, height - 3.0 * inch, data.get("service", ""))

    # Items Table
    table_data = [["Description", "Qty", "Unit Price", "Amount"]]
    for item in data.get("items", []):
        try:
            qty_val = float(item.get("qty") or 0)
            amount_val = float(item.get("amount") or 0)
            total = qty_val * amount_val
            table_data.append([
                item.get("description", ""),
                item.get("qty", ""),
                f"₱{amount_val:,.2f}",
                f"₱{total:,.2f}"
            ])
        except ValueError:
            pass

    # Add subtotal row
    subtotal = data.get("subtotal", "₱0.00")
    table_data.append(["", "", "Subtotal:", subtotal])

    table = Table(table_data, colWidths=[3.5*inch, 0.8*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4B8DF8")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#DDDDDD")),
        ('FONTNAME', (0, -1), (-2, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-2, -1), colors.HexColor("#F5F5F5")),
    ]))
    table.wrapOn(c, width, height)
    table.drawOn(c, 1 * inch, height - 5 * inch)

    # Footer
    if data.get("attorney"):
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 0.5 * inch, f"Prepared by: {data['attorney']}")

    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 0.25 * inch, "Thank you for your business!")

    c.save()
