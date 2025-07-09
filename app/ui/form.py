import customtkinter as ctk
from datetime import datetime
import re
import tempfile
import os
from reportlab.lib.pagesizes import legal, letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import webbrowser

def create_billing_form(master):
    # Modern theme configuration
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    
    # Main container with scrollable frame
    main_frame = ctk.CTkFrame(master, corner_radius=15)
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)
    
    # Create scrollable container
    scroll_frame = ctk.CTkScrollableFrame(main_frame)
    scroll_frame.pack(fill="both", expand=True)
    
    # Validation functions
    def validate_required(text):
        return len(text.strip()) > 0
    
    def validate_currency(text):
        try:
            if text:
                float(text)
            return True
        except ValueError:
            return False
    
    def validate_quantity(text):
        try:
            if text:
                qty = float(text)
                return qty > 0
            return True
        except ValueError:
            return False
    
    def validate_date(text):
        try:
            if text:
                datetime.strptime(text, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    def validate_name(text):
        return bool(re.match(r"^[a-zA-Z\s\-\.']+$", text)) if text else True
    
    # Store validation references
    validation_errors = {}
    error_labels = {}
    
    def show_error(field_name, message):
        if field_name in error_labels:
            error_labels[field_name].configure(text=message)
        validation_errors[field_name] = message
    
    def clear_error(field_name):
        if field_name in error_labels:
            error_labels[field_name].configure(text="")
        if field_name in validation_errors:
            del validation_errors[field_name]
    
    def validate_form():
        # Clear previous errors
        for field in list(validation_errors.keys()):
            clear_error(field)
        
        # Validate required fields
        if not validate_required(entry_receiver.get()):
            show_error("receiver", "Your name/company is required")
        
        if not validate_required(entry_name.get()):
            show_error("client_name", "Client name is required")
        elif not validate_name(entry_name.get()):
            show_error("client_name", "Invalid client name")
        
        if not validate_date(entry_date.get()):
            show_error("client_date", "Invalid date format (YYYY-MM-DD)")
        
        if not validate_required(entry_service.get()):
            show_error("service", "Service description is required")
        
        if entry_attorney.get() and not validate_name(entry_attorney.get()):
            show_error("attorney", "Invalid attorney name")
        
        # Validate billing items
        valid_items = []
        for i, child in enumerate(items_frame.winfo_children()):
            if isinstance(child, ctk.CTkFrame) and hasattr(child, 'is_item_frame'):
                desc = child.desc_entry.get()
                qty = child.qty_entry.get()
                amount = child.amount_entry.get()
                
                if desc:  # Only validate if description exists
                    if not validate_quantity(qty):
                        show_error(f"item_qty_{i}", "Quantity must be positive number")
                    if not validate_currency(amount):
                        show_error(f"item_amount_{i}", "Invalid amount")
                    valid_items.append(True)
        
        if not any(valid_items):
            show_error("items", "At least one valid billing item is required")
        
        return len(validation_errors) == 0
    
    # Header section
    header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=15)
    
    title = ctk.CTkLabel(
        header_frame, 
        text="INVOICE GENERATOR", 
        font=("Segoe UI Semibold", 22)
    )
    title.pack(side="left")
    
    date_badge = ctk.CTkLabel(
        header_frame,
        text=datetime.now().strftime("%d %b %Y"),
        font=("Segoe UI", 10),
        corner_radius=10,
        fg_color=("#E1E1E1", "#3A3A3A"),
        padx=10,
        pady=2
    )
    date_badge.pack(side="right")
    
    # Form sections function
    def create_section(parent, title_text):
        frame = ctk.CTkFrame(parent, corner_radius=12, border_width=1)
        frame.pack(fill="x", padx=15, pady=8)
        
        if title_text:
            section_title = ctk.CTkLabel(
                frame, 
                text=title_text,
                font=("Segoe UI Semibold", 12),
                anchor="w",
                padx=10,
                pady=10
            )
            section_title.pack(fill="x")
        
        return frame
    
    # Error label creator
    def create_error_label(parent, field_name):
        error_label = ctk.CTkLabel(
            parent,
            text="",
            text_color="#FF5555",
            font=("Segoe UI", 10),
            anchor="w"
        )
        error_labels[field_name] = error_label
        return error_label
    
    # Personal Information Section
    personal_frame = create_section(scroll_frame, "YOUR INFORMATION")
    
    entry_receiver = ctk.CTkEntry(
        personal_frame, 
        placeholder_text="Your Name / Company*",
        font=("Segoe UI", 12),
        height=38,
        corner_radius=8
    )
    entry_receiver.pack(fill="x", padx=10, pady=(0, 0))
    create_error_label(personal_frame, "receiver").pack(fill="x", padx=10, pady=(0, 10))
    
    entry_position = ctk.CTkEntry(
        personal_frame, 
        placeholder_text="Position / Title",
        font=("Segoe UI", 12),
        height=38,
        corner_radius=8
    )
    entry_position.pack(fill="x", padx=10, pady=(0, 5))
    
    # Client Information Section
    client_frame = create_section(scroll_frame, "CLIENT INFORMATION")
    
    client_grid = ctk.CTkFrame(client_frame, fg_color="transparent")
    client_grid.pack(fill="x", padx=10, pady=5)
    client_grid.columnconfigure(0, weight=1)
    client_grid.columnconfigure(1, weight=1)
    
    entry_name = ctk.CTkEntry(
        client_grid, 
        placeholder_text="Client Name*",
        font=("Segoe UI", 12),
        height=38,
        corner_radius=8
    )
    entry_name.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
    create_error_label(client_frame, "client_name").pack(fill="x", padx=10, pady=(0, 5))
    
    entry_date = ctk.CTkEntry(
        client_grid, 
        placeholder_text=datetime.now().strftime("%Y-%m-%d"),
        font=("Segoe UI", 12),
        height=38,
        corner_radius=8
    )
    entry_date.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ew")
    create_error_label(client_frame, "client_date").pack(fill="x", padx=10, pady=(0, 5))
    
    # Service Details Section
    service_frame = create_section(scroll_frame, "SERVICE DETAILS")
    
    entry_service = ctk.CTkEntry(
        service_frame,
        placeholder_text="Service Description*",
        font=("Segoe UI", 12),
        height=38,
        corner_radius=8
    )
    entry_service.pack(fill="x", padx=10, pady=(0, 0))
    create_error_label(service_frame, "service").pack(fill="x", padx=10, pady=(0, 5))
    
    # Billing Statement Section
    billing_frame = create_section(scroll_frame, "BILLING STATEMENT")
    create_error_label(billing_frame, "items").pack(fill="x", padx=10, pady=(0, 5))
    
    # Items table header
    header_grid = ctk.CTkFrame(billing_frame, fg_color="transparent")
    header_grid.pack(fill="x", padx=10, pady=(0, 5))
    header_grid.columnconfigure(0, weight=3)
    header_grid.columnconfigure(1, weight=1)
    header_grid.columnconfigure(2, weight=1)
    header_grid.columnconfigure(3, weight=0)
    
    ctk.CTkLabel(header_grid, text="Description", font=("Segoe UI Semibold", 11)).grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(header_grid, text="Qty", font=("Segoe UI Semibold", 11)).grid(row=0, column=1, sticky="e")
    ctk.CTkLabel(header_grid, text="Amount", font=("Segoe UI Semibold", 11)).grid(row=0, column=2, sticky="e")
    ctk.CTkLabel(header_grid, text="", width=40).grid(row=0, column=3)
    
    # Items list
    items_frame = ctk.CTkFrame(billing_frame, fg_color="transparent")
    items_frame.pack(fill="x", padx=10, pady=5)
    
    # Function to add new item row
    def add_item_row(description="", qty="1", amount=""):
        item_frame = ctk.CTkFrame(items_frame, fg_color="transparent")
        item_frame.pack(fill="x", pady=2)
        item_frame.is_item_frame = True
        
        item_frame.columnconfigure(0, weight=3)
        item_frame.columnconfigure(1, weight=1)
        item_frame.columnconfigure(2, weight=1)
        item_frame.columnconfigure(3, weight=0)
        
        # Description entry
        entry_desc = ctk.CTkEntry(
            item_frame, 
            placeholder_text="Item description",
            font=("Segoe UI", 11),
            height=32,
            corner_radius=6
        )
        entry_desc.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        entry_desc.insert(0, description)
        item_frame.desc_entry = entry_desc
        
        # Quantity entry
        entry_qty = ctk.CTkEntry(
            item_frame, 
            placeholder_text="Qty",
            font=("Segoe UI", 11),
            height=32,
            corner_radius=6,
            width=60,
            validate="key",
            validatecommand=(master.register(lambda text: validate_quantity(text) or text == ""), "%P")
        )
        entry_qty.grid(row=0, column=1, padx=5, sticky="e")
        entry_qty.insert(0, qty)
        item_frame.qty_entry = entry_qty
        
        # Amount entry
        entry_amount = ctk.CTkEntry(
            item_frame, 
            placeholder_text="0.00",
            font=("Segoe UI", 11),
            height=32,
            corner_radius=6,
            width=100,
            validate="key",
            validatecommand=(master.register(lambda text: validate_currency(text) or text == ""), "%P")
        )
        entry_amount.grid(row=0, column=2, padx=(5, 0), sticky="e")
        entry_amount.insert(0, amount)
        item_frame.amount_entry = entry_amount
        
        # Remove button
        def remove_item():
            item_frame.destroy()
            update_totals()
        
        remove_btn = ctk.CTkButton(
            item_frame,
            text="×",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            text_color="#FF5555",
            hover_color="#330000",
            font=("Segoe UI", 14, "bold"),
            command=remove_item
        )
        remove_btn.grid(row=0, column=3, padx=(5, 0))
        
        # Error label for the row
        row_error = ctk.CTkLabel(
            item_frame,
            text="",
            text_color="#FF5555",
            font=("Segoe UI", 9),
            anchor="w"
        )
        row_error.grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 2))
        
        # Bind calculations to quantity/amount changes
        def calculate_total(*args):
            update_totals()
        
        entry_qty.bind("<KeyRelease>", calculate_total)
        entry_amount.bind("<KeyRelease>", calculate_total)
        
        return item_frame
    
    # Add initial item row
    add_item_row()
    
    # Add item button
    def on_add_item():
        add_item_row()
        update_totals()
    
    add_item_btn = ctk.CTkButton(
        billing_frame,
        text="+ Add Item",
        command=on_add_item,
        height=30,
        corner_radius=6,
        font=("Segoe UI", 10),
        fg_color="transparent",
        border_width=1
    )
    add_item_btn.pack(pady=(5, 10))
    
    # Totals section
    totals_frame = ctk.CTkFrame(billing_frame, fg_color="transparent")
    totals_frame.pack(fill="x", padx=10, pady=(5, 0))
    
    subtotal_label = ctk.CTkLabel(
        totals_frame,
        text="Subtotal:",
        font=("Segoe UI", 11),
        anchor="e"
    )
    subtotal_label.grid(row=0, column=0, sticky="e")
    
    subtotal_value = ctk.CTkLabel(
        totals_frame,
        text="₱0.00",
        font=("Segoe UI Semibold", 11),
        anchor="e"
    )
    subtotal_value.grid(row=0, column=1, padx=(10, 0), sticky="e")
    
    # Function to update totals
    def update_totals():
        subtotal = 0.0
        for child in items_frame.winfo_children():
            if isinstance(child, ctk.CTkFrame) and hasattr(child, 'is_item_frame'):
                qty_entry = child.qty_entry
                amount_entry = child.amount_entry
                
                try:
                    qty = float(qty_entry.get() or 0)
                    amount = float(amount_entry.get() or 0)
                    subtotal += qty * amount
                except ValueError:
                    pass
        
        subtotal_value.configure(text=f"₱{subtotal:,.2f}")
    
    # Payment Information Section
    payment_frame = create_section(scroll_frame, "PAYMENT INFORMATION")
    
    status_var = ctk.StringVar(value="pending")
    status_dropdown = ctk.CTkComboBox(
        payment_frame,
        values=["pending", "paid", "overdue"],
        variable=status_var,
        font=("Segoe UI", 12),
        height=38,
        corner_radius=8
    )
    status_dropdown.pack(fill="x", padx=10, pady=5)
    
    # Attorney Information
    attorney_frame = create_section(scroll_frame, "ATTORNEY INFORMATION")
    
    entry_attorney = ctk.CTkEntry(
        attorney_frame, 
        placeholder_text="Attorney Name",
        font=("Segoe UI", 12),
        height=38,
        corner_radius=8
    )
    entry_attorney.pack(fill="x", padx=10, pady=(0, 0))
    create_error_label(attorney_frame, "attorney").pack(fill="x", padx=10, pady=(0, 5))
    
    # PDF Generation Functions
    def generate_pdf(filepath=None):
        if not validate_form():
            messagebox.showerror("Validation Error", "Please fix all errors before generating PDF")
            return None
        
        if not filepath:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                title="Save Invoice As"
            )
            if not filepath:
                return None
        
        try:
            # Create PDF
            c = canvas.Canvas(filepath, pagesize=legal)
            width, height = legal
            
            # Styles
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
            c.drawString(1 * inch, height - 1.5 * inch, entry_receiver.get())
            if entry_position.get():
                c.drawString(1 * inch, height - 1.7 * inch, entry_position.get())
            
            # Invoice Details
            c.setFont("Helvetica", 10)
            c.drawRightString(width - 1 * inch, height - 1 * inch, f"Invoice Date: {entry_date.get()}")
            c.drawRightString(width - 1 * inch, height - 1.2 * inch, f"Status: {status_var.get().upper()}")
            
            # Client Info
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1 * inch, height - 2.2 * inch, "Bill To:")
            c.setFont("Helvetica", 10)
            c.drawString(1 * inch, height - 2.4 * inch, entry_name.get())
            
            # Service Description
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1 * inch, height - 2.8 * inch, "Service:")
            c.setFont("Helvetica", 10)
            c.drawString(1 * inch, height - 3.0 * inch, entry_service.get())
            
            # Items Table
            data = [["Description", "Qty", "Unit Price", "Amount"]]
            
            for child in items_frame.winfo_children():
                if isinstance(child, ctk.CTkFrame) and hasattr(child, 'is_item_frame'):
                    desc = child.desc_entry.get()
                    qty = child.qty_entry.get()
                    amount = child.amount_entry.get()
                    
                    if desc:
                        try:
                            qty_val = float(qty or 0)
                            amount_val = float(amount or 0)
                            total = qty_val * amount_val
                            data.append([
                                desc,
                                qty,
                                f"₱{amount_val:,.2f}",
                                f"₱{total:,.2f}"
                            ])
                        except ValueError:
                            pass
            
            # Add subtotal row
            subtotal = subtotal_value.cget("text")
            data.append(["", "", "Subtotal:", subtotal])
            
            # Create table
            table = Table(data, colWidths=[3.5*inch, 0.8*inch, 1*inch, 1*inch])
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
            
            # Draw table
            table.wrapOn(c, width, height)
            table.drawOn(c, 1 * inch, height - 5 * inch)
            
            # Footer
            if entry_attorney.get():
                c.setFont("Helvetica", 10)
                c.drawString(1 * inch, 0.5 * inch, f"Prepared by: {entry_attorney.get()}")
            
            c.setFont("Helvetica", 8)
            c.drawCentredString(width / 2, 0.25 * inch, "Thank you for your business!")
            
            c.save()
            return filepath
        except Exception as e:
            messagebox.showerror("PDF Error", f"Failed to generate PDF: {str(e)}")
            return None
    
    def preview_pdf():
        if not validate_form():
            messagebox.showerror("Validation Error", "Please fix all errors before previewing")
            return
        
        # Create temporary PDF
        temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_pdf.close()
        pdf_path = generate_pdf(temp_pdf.name)
        
        if pdf_path:
            # Open PDF in default viewer
            webbrowser.open(pdf_path)
    
    # Action Buttons
    button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
    button_frame.pack(fill="x", padx=15, pady=(10, 15))
    
    def on_generate():
        pdf_path = generate_pdf()
        if pdf_path:
            messagebox.showinfo("Success", f"Invoice saved to:\n{pdf_path}")
    
    btn_preview = ctk.CTkButton(
        button_frame,
        text="Preview Invoice",
        command=preview_pdf,
        height=40,
        corner_radius=8,
        font=("Segoe UI Semibold", 12),
        fg_color="transparent",
        border_width=1
    )
    btn_preview.pack(side="left", padx=(0, 10), fill="x", expand=True)
    
    btn_generate = ctk.CTkButton(
        button_frame,
        text="Save as PDF",
        command=on_generate,
        height=40,
        corner_radius=8,
        font=("Segoe UI Semibold", 12)
    )
    btn_generate.pack(side="right", fill="x", expand=True)
    
    return main_frame