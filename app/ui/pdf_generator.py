from reportlab.lib.pagesizes import legal, letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile
import os
from reportlab.lib.enums import TA_LEFT

# Add your PDF generation functions here. Example:
def generate_invoice_pdf(data, filename):
    c = canvas.Canvas(filename, pagesize=legal)
    width, height = legal
    margin_x = 1 * inch
    y = height - 1 * inch  # Top margin (for header)

    # Header (as document header, always at the very top)
    if data.get("header"):
        from reportlab.platypus import Paragraph, Frame
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        header_style = ParagraphStyle('Header', fontName="Helvetica-Bold", fontSize=14, leading=18, alignment=1, textColor=colors.black)  # Centered
        header = Paragraph(data["header"].replace("\n", "<br/>"), header_style)
        header_height = max(0.7 * inch, 0.22 * inch * (data["header"].count("\n") + 1))
        header_frame = Frame(margin_x, height - header_height - 0.5 * inch, width - 2 * margin_x, header_height, showBoundary=0)
        header_frame.addFromList([header], c)
        y = height - header_height - 0.7 * inch
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0, 0)



    # Name, Date, Re
    c.drawString(margin_x, y, f"Name: {data.get('client_name', '')}")
    y -= 0.32 * inch

    # Format date as 'Month Day, Year' (e.g., July 10, 2025)
    import datetime
    raw_date = data.get('date', '')
    formatted_date = raw_date
    try:
        # Try MM-DD-YYYY
        dt = datetime.datetime.strptime(raw_date, '%m-%d-%Y')
        formatted_date = dt.strftime('%B %d, %Y')
    except Exception:
        try:
            # Try YYYY-MM-DD
            dt = datetime.datetime.strptime(raw_date, '%Y-%m-%d')
            formatted_date = dt.strftime('%B %d, %Y')
        except Exception:
            pass
    c.drawString(margin_x, y, f"Date: {formatted_date}")
    y -= 0.32 * inch
    c.drawString(margin_x, y, f"Re: {data.get('service', '')}")
    y -= 0.45 * inch

    # Divider
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.7)
    c.line(margin_x, y, width - margin_x, y)
    y -= 0.4 * inch

    # Body Message
    if data.get("body_message"):
        from reportlab.platypus import Paragraph, Frame
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        body_style = ParagraphStyle('Body', fontName="Helvetica", fontSize=12, leading=18, textColor=colors.black)
        body = Paragraph(data["body_message"].replace("\n", "<br/>"), body_style)
        body_height = 1.5 * inch
        body_frame = Frame(margin_x, y - body_height, width - 2 * margin_x, body_height, showBoundary=0)
        body_frame.addFromList([body], c)
        y -= body_height + 0.2 * inch
    else:
        y -= 0.2 * inch

    # Divider
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.7)
    c.line(margin_x, y, width - margin_x, y)
    y -= 0.5 * inch

    # BILLING STATEMENT title (centered, bold, underlined)
    c.setFont("Helvetica-Bold", 18)
    title = "BILLING STATEMENT"
    title_width = c.stringWidth(title, "Helvetica-Bold", 18)
    c.drawString((width - title_width) / 2, y, title)
    c.setLineWidth(1.2)
    c.setStrokeColorRGB(0, 0, 0)
    c.line((width - title_width) / 2, y - 3, (width + title_width) / 2, y - 3)
    y -= 0.5 * inch

    # Table
    table_data = [["Description", "Qty", "Unit Price", "Amount"]]
    for item in data.get("items", []):
        try:
            qty_val = float(item.get("qty") or 0)
            amount_val = float(item.get("amount") or 0)
            total = qty_val * amount_val
            table_data.append([
                item.get("description", ""),
                item.get("qty", ""),
                f"PHP {int(amount_val):,}",
                f"PHP {int(total):,}"
            ])
        except ValueError:
            pass
    subtotal = data.get("subtotal", "PHP 0")
    if isinstance(subtotal, str) and "." in subtotal:
        subtotal = subtotal.split(".")[0]
    table_data.append(["", "", "Subtotal:", subtotal])

    # Calculate responsive column widths based on available width
    available_width = width - 2 * margin_x
    desc_col = 0.36 * available_width
    qty_col = 0.13 * available_width
    unit_col = 0.25 * available_width
    amt_col = 0.26 * available_width

    # Wrap long description text before creating the Table
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    desc_style = ParagraphStyle('desc', fontName="Helvetica", fontSize=11, leading=13, alignment=TA_LEFT)
    for i in range(1, len(table_data)):
        desc = table_data[i][0]
        if isinstance(desc, str) and len(desc) > 40:
            table_data[i][0] = Paragraph(desc, desc_style)
    table = Table(table_data, colWidths=[desc_col, qty_col, unit_col, amt_col])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, (0.7,0.7,0.7)),
        ('BACKGROUND', (0, 0), (-1, 0), (0.95, 0.95, 0.95)),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    table_height = (len(table_data) + 1) * 0.32 * inch
    table.wrapOn(c, width, height)
    table.drawOn(c, margin_x, y - table_height)
    y -= table_height + 0.5 * inch

    # Divider
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.7)
    c.line(margin_x, y, width - margin_x, y)
    y -= 0.4 * inch

    # Company Contact (centered, bold, with space)
    if data.get("company_contact"):
        from reportlab.platypus import Paragraph, Frame
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        contact_style = ParagraphStyle('Contact', fontName="Helvetica-Bold", fontSize=12, leading=16, alignment=1, textColor=colors.black)  # 1=center
        contact = Paragraph(data["company_contact"].replace("\n", "<br/>"), contact_style)
        contact_height = max(0.8 * inch, 0.25 * inch * (data["company_contact"].count("\n") + 1))
        contact_frame = Frame(margin_x, y - contact_height, width - 2 * margin_x, contact_height, showBoundary=0)
        contact_frame.addFromList([contact], c)
        y -= contact_height + 0.5 * inch  # Extra space after

    # Prepared By (left-aligned, not bold)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Prepared By:")
    y -= 0.28 * inch
    c.setFont("Helvetica", 12)
    receiver = data.get("receiver", "")
    if receiver:
        c.drawString(margin_x, y, receiver)
        y -= 0.28 * inch
    position = data.get("position")
    if position:
        c.drawString(margin_x, y, position)
        y -= 0.28 * inch

    # Noted By (left-aligned, not bold)
    if data.get("attorney"):
        y -= 0.18 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, y, "Noted By:")
        y -= 0.28 * inch
        c.setFont("Helvetica", 12)
        c.drawString(margin_x, y, data["attorney"])


    # Footer (as paragraph, at the bottom)
    if data.get("footer"):
        from reportlab.platypus import Paragraph, Frame
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        footer_style = ParagraphStyle('Footer', fontName="Helvetica", fontSize=11, leading=15, alignment=1, textColor=colors.grey)
        footer = Paragraph(data["footer"].replace("\n", "<br/>"), footer_style)
        footer_height = max(0.5 * inch, 0.18 * inch * (data["footer"].count("\n") + 1))
        footer_frame = Frame(margin_x, 0.7 * inch, width - 2 * margin_x, footer_height, showBoundary=0)
        footer_frame.addFromList([footer], c)

    c.save()
