from reportlab.lib.pagesizes import legal, letter, A4
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
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    margin_x = 0.75 * inch  # Slightly smaller margin for A4
    y = height - 0.75 * inch  # Top margin (for header)

    # Logo (top right, persistent)
    logo_path = data.get("logo_path")
    logo_max_width = 1.2 * inch  # Slightly smaller for A4
    logo_max_height = 0.8 * inch
    logo_margin_top = 0.2 * inch
    logo_margin_right = 0.7 * inch
    if logo_path:
        if os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                logo = ImageReader(logo_path)
                img_width, img_height = logo.getSize()
                aspect = img_width / img_height
                # Fit logo inside the bounding box (never exceed either dimension)
                scale = min(logo_max_width / img_width, logo_max_height / img_height)
                draw_width = img_width * scale
                draw_height = img_height * scale
                # Center vertically in the allowed box
                y_logo = height - logo_margin_top - ((logo_max_height - draw_height) / 2) - draw_height
                c.drawImage(
                    logo,
                    width - logo_margin_right - draw_width,
                    y_logo,
                    width=draw_width,
                    height=draw_height,
                    mask='auto',
                    preserveAspectRatio=True
                )
            except Exception as e:
                c.setFont("Helvetica", 8)
                c.setFillColorRGB(1, 0, 0)
                c.drawString(width - logo_margin_right - logo_max_width, height - logo_margin_top - 10, f"[Logo error: {str(e)[:30]}]")
                c.setFillColorRGB(0, 0, 0)
        else:
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(1, 0, 0)
            c.drawString(width - logo_margin_right - logo_max_width, height - logo_margin_top - 10, "[Logo not found]")
            c.setFillColorRGB(0, 0, 0)

    # Header (first line bold, next lines as subheader)
    header_height_used = 0
    if data.get("header"):
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        max_header_height = height / 3.5  # Slightly less for A4
        # Split header into lines
        header_lines = data["header"].split("\n")
        first_line = header_lines[0] if len(header_lines) > 0 else ""
        second_line = header_lines[1] if len(header_lines) > 1 else ""
        third_line = header_lines[2] if len(header_lines) > 2 else ""
        # Reserve space for logo on the right
        right_margin_for_logo = logo_max_width + logo_margin_right + 0.1 * inch
        available_header_width = width - margin_x - right_margin_for_logo
        # Styles
        first_style = ParagraphStyle('HeaderBold', fontName="Helvetica-Bold", fontSize=15, leading=18, alignment=0, textColor=colors.black)
        sub_style = ParagraphStyle('HeaderSub', fontName="Helvetica", fontSize=10, leading=12, alignment=0, textColor=colors.black)
        # Paragraphs
        para_first = Paragraph(first_line, first_style)
        para_second = Paragraph(second_line, sub_style) if second_line else None
        para_third = Paragraph(third_line, sub_style) if third_line else None
        # Calculate heights
        w1, h1 = para_first.wrap(available_header_width, max_header_height)
        h_total = h1
        w2 = w3 = 0
        h2 = h3 = 0
        if para_second:
            w2, h2 = para_second.wrap(available_header_width, max_header_height - h_total)
            h_total += h2
        if para_third:
            w3, h3 = para_third.wrap(available_header_width, max_header_height - h_total)
            h_total += h3
        # Draw header lines
        header_y = height - h_total - 0.25 * inch
        y_cursor = header_y + h_total
        para_first.drawOn(c, margin_x, y_cursor - h1)
        y_cursor -= h1
        if para_second:
            para_second.drawOn(c, margin_x, y_cursor - h2)
            y_cursor -= h2
        if para_third:
            para_third.drawOn(c, margin_x, y_cursor - h3)
            y_cursor -= h3
        y = header_y - 0.5 * inch  # Less space after header for A4
        header_height_used = h_total + 0.4 * inch
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0, 0, 0)



    # Name, Date, Re
    c.drawString(margin_x, y, f"Attention: {data.get('client_name', '')} ")
    y -= 0.28 * inch

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
    y -= 0.28 * inch
    c.drawString(margin_x, y, f"Re: {data.get('service', '')}")
    y -= 0.35 * inch

    # Divider
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.6)
    c.line(margin_x, y, width - margin_x, y)
    y -= 0.3 * inch

    # Body Message (dynamic height, supports overflow to new page)
    from reportlab.platypus import Paragraph, Frame
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    body_message = data.get("body_message", "")
    body_style = ParagraphStyle('Body', fontName="Helvetica", fontSize=11, leading=16, textColor=colors.black)
    if body_message:
        body = Paragraph(body_message.replace("\n", "<br/>"), body_style)
        avail_height = y - 0.75 * inch  # Reserve bottom margin
        w, h = body.wrap(width - 2 * margin_x, avail_height)
        if h <= avail_height:
            body.drawOn(c, margin_x, y - h)
            y -= h + 0.15 * inch
        else:
            # Split and render across pages
            story = body.split(width - 2 * margin_x, avail_height)
            for part in story:
                part_h = part.height
                if part_h > avail_height:
                    part_h = avail_height
                part.drawOn(c, margin_x, y - part_h)
                y -= part_h
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 0.75 * inch
                avail_height = y - 0.75 * inch
            y -= 0.15 * inch
    else:
        y -= 0.15 * inch


    # --- Move BILLING STATEMENT section above contact info ---
    # Divider
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.6)
    c.line(margin_x, y, width - margin_x, y)
    y -= 0.35 * inch

    # BILLING STATEMENT title (centered, bold, underlined, black)
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0, 0, 0)
    title = "BILLING STATEMENT"
    title_width = c.stringWidth(title, "Helvetica-Bold", 18)
    c.drawString((width - title_width) / 2, y, title)
    c.setLineWidth(1.2)
    c.setStrokeColorRGB(0, 0, 0)
    c.line((width - title_width) / 2, y - 3, (width + title_width) / 2, y - 3)
    y -= 0.35 * inch

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
    desc_col = 0.38 * available_width
    qty_col = 0.13 * available_width
    unit_col = 0.23 * available_width
    amt_col = 0.26 * available_width

    # Wrap long description text before creating the Table
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    desc_style = ParagraphStyle('desc', fontName="Helvetica", fontSize=10, leading=12, alignment=TA_LEFT)
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

    table_height = (len(table_data) + 1) * 0.28 * inch
    table.wrapOn(c, width, height)
    table.drawOn(c, margin_x, y - table_height)
    y -= table_height + 0.35 * inch

    # --- Contact Information Section (after billing statement) ---
    # Divider
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.6)
    c.line(margin_x, y, width - margin_x, y)
    y -= 0.35 * inch

    # Contact Message (black, centered)
    contact_message = data.get("contact_message", "")
    if contact_message:
        contact_message_style = ParagraphStyle('ContactMsg', fontName="Helvetica", fontSize=10, leading=14, alignment=1, textColor=colors.black)
        contact_msg = Paragraph(contact_message.replace("\n", "<br/>"), contact_message_style)
        avail_height = y - 0.75 * inch
        w, h = contact_msg.wrap(width - 2 * margin_x, avail_height)
        if h <= avail_height:
            contact_msg.drawOn(c, margin_x, y - h)
            y -= h + 0.1 * inch
        else:
            # Split and render across pages
            story = contact_msg.split(width - 2 * margin_x, avail_height)
            for part in story:
                part_h = part.height
                if part_h > avail_height:
                    part_h = avail_height
                part.drawOn(c, margin_x, y - part_h)
                y -= part_h
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 0.75 * inch
                avail_height = y - 0.75 * inch
            y -= 0.1 * inch

    # Company Contact (black, centered)
    company_contact = data.get("company_contact", "")
    contact_style = ParagraphStyle('Contact', fontName="Helvetica-Bold", fontSize=11, leading=14, alignment=1, textColor=colors.black)
    if company_contact:
        contact = Paragraph(company_contact.replace("\n", "<br/>"), contact_style)
        avail_height = y - 0.75 * inch
        w, h = contact.wrap(width - 2 * margin_x, avail_height)
        if h <= avail_height:
            contact.drawOn(c, margin_x, y - h)
            y -= h + 0.3 * inch
        else:
            # Split and render across pages
            story = contact.split(width - 2 * margin_x, avail_height)
            for part in story:
                part_h = part.height
                if part_h > avail_height:
                    part_h = avail_height
                part.drawOn(c, margin_x, y - part_h)
                y -= part_h
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 0.75 * inch
                avail_height = y - 0.75 * inch
            y -= 0.3 * inch

    # --- Calculate footer height, but do not draw yet ---
    footer_height = 0
    footer_obj = None
    if data.get("footer"):
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        max_footer_height = height / 3.5
        min_font_size = 7
        font_size = 8
        leading = 13
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
        footer_obj = footer
        footer_height = h

    # Place Prepared By and Noted By exactly 1 inch above the bottom
    prepared_y = 2.30 * inch 
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, prepared_y, "Prepared By:")
    c.setFont("Helvetica", 11)
    receiver = data.get("receiver", "")
    pos_y = prepared_y - 0.22 * inch
    if receiver:
        c.drawString(margin_x, pos_y, receiver)
        pos_y -= 0.22 * inch
    position = data.get("position")
    if position:
        c.drawString(margin_x, pos_y, position)
        pos_y -= 0.22 * inch

    # Noted By (left-aligned, not bold, below Prepared By)
    if data.get("attorney"):
        pos_y -= 0.19 * inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin_x, pos_y, "Noted By:")
        pos_y -= 0.27 * inch
        c.setFont("Helvetica", 11)
        c.drawString(margin_x, pos_y, data["attorney"])

    # Now draw the footer at the very bottom
    if footer_obj:
        footer_y = 0.15 * inch
        footer_obj.drawOn(c, margin_x, footer_y)

    c.save()
