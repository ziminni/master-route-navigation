# date_utils.py
from datetime import datetime

def format_date_display(date_str):
    """Centralized date formatting for consistent display across all views"""
    if not date_str:
        return ""
    
    # If it's already in "Oct 14" format, return as is
    if len(date_str) <= 6 and any(month in date_str.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
        return date_str
    
    # Try multiple date formats
    date_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S", 
        "%Y-%m-%d",
        "%b %d",
        "%d/%m/%Y",
        "%m/%d/%Y"
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%b %d")
        except ValueError:
            continue
    
    return date_str.split(" ")[0] if " " in date_str else date_str