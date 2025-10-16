import os

def load_qss(app):
    """Load and apply the QSS for Module 3 (Academic Schedule) to the QApplication."""
    qss_path = os.path.join(os.path.dirname(__file__), '../assets/qss/module3_styles.qss')
    qss_path = os.path.abspath(qss_path)
    if os.path.exists(qss_path):
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    else:
        print(f"QSS file not found: {qss_path}")
