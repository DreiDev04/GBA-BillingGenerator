# app/main.py

import customtkinter as ctk
from app.ui.form import create_billing_form  # We'll build this next in Step 3

def start_app():
    # Setup appearance and theme
    ctk.set_appearance_mode("System")          # Options: "System", "Light", "Dark"
    ctk.set_default_color_theme("blue")        # Options: "blue", "green", etc.

    # Create the main window
    root = ctk.CTk()
    root.title("GBA Law Office - Billing Invoice Generator")
    root.geometry("1280x720")

    # Add the billing form from ui/form.py
    form = create_billing_form(master=root)
    form.pack(padx=20, pady=20, fill="both", expand=True)

    # Run the app
    root.mainloop()
