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

    # Header (dynamic height, up to 1/3 page, always starts at top margin)
    header_height_used = 0
    if data.get("header"):
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        max_header_height = height / 3
        min_font_size = 8
        font_size = 14
        leading = 18
        header_text = data["header"].replace("\n", "<br/>")
        while font_size >= min_font_size:
            header_style = ParagraphStyle('Header', fontName="Helvetica-Bold", fontSize=font_size, leading=leading, alignment=1, textColor=colors.black)
            header = Paragraph(header_text, header_style)
            w, h = header.wrap(width - 2 * margin_x, max_header_height)
            if h <= max_header_height:
                break
            font_size -= 2
            leading = max(leading - 2, font_size + 2)
        else:
            header_text = header_text[:1500] + "<br/><b>...(truncated)</b>" if len(header_text) > 1500 else header_text
            header = Paragraph(header_text, header_style)
            w, h = header.wrap(width - 2 * margin_x, max_header_height)
        # Draw header at the very top of the page (like DOCX)
        header_y = height - h - 0.4 * inch
        header.drawOn(c, margin_x, header_y)
        y = header_y - 0.2 * inch
        header_height_used = h + 0.2 * inch
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


    # Footer (dynamic height, up to 1/3 page, always starts at bottom margin)
    footer_height_used = 0
    if data.get("footer"):
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        max_footer_height = height / 3
        min_font_size = 8
        font_size = 8
        leading = 15
        footer_text = data["footer"].replace("\n", "<br/>")
        while font_size >= min_font_size:
            footer_style = ParagraphStyle('Footer', fontName="Helvetica", fontSize=font_size, leading=leading, alignment=1, textColor=colors.grey)
            footer = Paragraph(footer_text, footer_style)
            w, h = footer.wrap(width - 2 * margin_x, max_footer_height)
            if h <= max_footer_height:
                break
            font_size -= 2
            leading = max(leading - 2, font_size + 2)
        else:
            footer_text = footer_text[:1500] + "<br/><b>...(truncated)</b>" if len(footer_text) > 1500 else footer_text
            footer = Paragraph(footer_text, footer_style)
            w, h = footer.wrap(width - 2 * margin_x, max_footer_height)
        # Draw footer at the very bottom of the page (like DOCX)
        footer_y = 0.2 * inch
        footer.drawOn(c, margin_x, footer_y)
        footer_height_used = h + footer_y

    c.save()
