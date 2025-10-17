import sys
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QApplication, QMainWindow

# Import your main class (adjust the import path as needed)
from Student_Appointment_main_ui import Student_Ui_MainWindow

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Appointment System - Test")
        self.resize(1200, 800)
        
        # Create your widget
        self.student_ui = Student_Ui_MainWindow(
            username="john_doe",
            roles=["student"],
            primary_role="student",
            token="test_token_123"
        )
        
        # Set up the UI
        self.student_ui.setupUi(self)
        
        # Center the window on screen
        self.center_on_screen()

    def center_on_screen(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        self.move(
            (screen.width() - window_size.width()) // 2,
            (screen.height() - window_size.height()) // 2
        )

def main():
    app = QApplication(sys.argv)
    
    # Set application-wide styles (optional)
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()