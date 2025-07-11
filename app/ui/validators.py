import re
from datetime import datetime

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
            # Accept both MM-DD-YYYY and YYYY-MM-DD
            try:
                datetime.strptime(text, "%m-%d-%Y")
            except ValueError:
                datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_name(text):
    return bool(re.match(r"^[a-zA-Z\s\-\.']+$", text)) if text else True
