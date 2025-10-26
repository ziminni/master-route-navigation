"""
Centralized stylesheet constants for the custom widgets.
"""

# Dialog Styles
CONFIRM_STYLE = """
    border: 2px solid #084924; 
    background-color: #084924;
    border-radius: 10px;
    padding: 5px;
    color: white;
"""
CANCEL_STYLE = """
    border: 2px solid #EB5757; 
    background-color: #EB5757;
    border-radius: 10px;
    padding: 5px;
    color: white;
"""
BROWSE_STYLE = """
    border: 2px solid #084924; 
    background-color: transparent;
    border-radius: 10px;
    padding: 5px;
    color: #084924;
"""
EDIT_STYLE = "border-radius: 10px; padding: 10px; border: 1px solid #084924; color: #084924;"
LABEL_STYLE = "color: #084924; text-decoration: underline #084924;"
DIALOG_STYLE = """
    QDialog {
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 10px;
        padding: 10px;
    }
"""

# Card Button Styles
STYLE_GREEN_BTN = "background-color: #084924; color: white; border-radius: 5px; padding-top: 10px;padding-bottom: 10px; font-weight: bold;"
STYLE_RED_BTN = "background-color: #EB5757; color: white; border-radius: 5px; padding-top: 10px;padding-bottom: 10px; font-weight: bold;"
STYLE_PRIMARY_BTN = "background-color: #084924; color: white; border-radius: 5px;"
STYLE_YELLOW_BTN = "background-color: #FDC601; color: white; border-radius: 5px; padding-top: 10px;padding-bottom: 10px; font-weight: bold;"
STYLE_OFFICER_BTN = "background-color: #FFD700; color: black; border-radius: 5px; font-weight: bold;" # For OfficerCard