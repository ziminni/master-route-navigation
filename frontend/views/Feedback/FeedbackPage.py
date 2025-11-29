import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QTextEdit,
    QPushButton, QHBoxLayout, QFrame, QStyledItemDelegate, QApplication, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtSvgWidgets import QSvgWidget

class CenterDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        font = option.font
        font.setItalic(False)
        option.font = font

class MessageSentPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 3px solid #084924;
                border-radius: 12px;
            }
        """)
        container.setObjectName("container")
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setContentsMargins(60, 60, 60, 60)

        # Image path
        BASE_DIR = Path(__file__).resolve().parents[3]
        ASSETS_DIR = BASE_DIR / "frontend" / "assets" / "images"
        smile_path = ASSETS_DIR / "smile.svg"

        icon_widget = QSvgWidget(str(smile_path))
        icon_widget.setFixedSize(100, 100)
        icon_widget.setStyleSheet("background: transparent;")
        container_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        message_label = QLabel("Message sent!")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            font-size: 40px;
            font-weight: 900;
            color: rgba(8, 73, 36, 204);
            font-family: 'Inter';
            border: none;
        """)
        container_layout.addWidget(message_label)
        message_label_font = message_label.font()
        message_label_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 91)
        message_label.setFont(message_label_font)

        subtext_label = QLabel("Thank you for your honest feedback")
        subtext_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtext_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
            color: rgba(8, 73, 36, 204);
            font-family: 'Inter';
            border: none;
        """)
        container_layout.addWidget(subtext_label)

        outer_layout.addWidget(container)
        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.center().x() - self.width() // 2
        y = screen.center().y() - self.height() // 2
        self.move(x, y)

class FeedbackBox(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FeedbackPage")
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setStyleSheet("background-color: transparent;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 3px solid #0b3d0b;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        header = QHBoxLayout()
        header.setContentsMargins(0, 30, 0, 0)

        header.addStretch()

        title = QLabel("SUGGESTION, COMPLAINT, & FEEDBACK BOX")
        title.setStyleSheet("""
            QLabel {
                font-family: 'Poppins';
                font-size: 32px;
                font-weight: 1000;
                color: rgba(8, 73, 36, 204);
                border: none;
                background-color: transparent;
            }
        """)
        title.setFixedHeight(40)
        title_font = title.font()
        title_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 91)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)

        header.addStretch()
        layout.addLayout(header)
        layout.addSpacing(15)

        close_btn = QPushButton("✕", container)
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #036800;
                color: white;
                font-size: 14px;
                border-radius: 15px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #124d12;
            }
        """)
        close_btn.clicked.connect(self.animate_close)
        self.close_btn = close_btn
        self.container = container

        type_row = QHBoxLayout()
        type_row.setSpacing(5)
        type_label = QLabel("Type:")
        type_label.setStyleSheet("""
            font-family: 'Inter';
            font-size: 14px;
            font-weight: 600;
            color: #333333;
            border: none;
        """)
        type_row.addWidget(type_label)

        self.type_dropdown = QComboBox()
        self.type_dropdown.addItems(["Suggestion", "Complaint", "Feedback"])
        self.type_dropdown.setCurrentIndex(-1)
        self.type_dropdown.setPlaceholderText("Submission Type")
        self.type_dropdown.setItemDelegate(CenterDelegate(self.type_dropdown))
        self.type_dropdown.currentIndexChanged.connect(self.update_dropdown_style)
        self.update_dropdown_style()
        type_row.addWidget(self.type_dropdown)
        type_row.addStretch()
        layout.addLayout(type_row)

        subject = QLineEdit()
        subject.setFixedHeight(50)
        subject.setStyleSheet("""
            font-family: 'Inter';
            font-size: 14px;
            padding: 8px;
            border: 1px solid #275D38;
            border-radius: 10px;
        """)
        layout.addWidget(subject)
        self.subject_input = subject

        message = QTextEdit()
        message.setFixedHeight(250)
        message.setStyleSheet("""
            font-family: 'Inter';
            font-size: 14px;
            padding: 8px;
            border: 1px solid #275D38;
            border-radius: 10px;
        """)
        layout.addWidget(message)
        self.message_input = message

        submit_btn = QPushButton("SUBMIT MESSAGE")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                font-family: 'Inter';
                font-size: 14px;
                font-weight: 700;
                padding: 12px 60px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0a5529;
            }
        """)
        submit_btn.clicked.connect(self.submit_feedback)
        layout.addWidget(submit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(container)
        self.center_on_screen()
        
        # Setup animations
        self.setup_animations()

    def setup_animations(self):
        # Fade animation for smooth appearance
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Scale animation for smooth zoom effect
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(350)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutBack)

    def showEvent(self, event):
        super().showEvent(event)
        # Start smooth animations
        self.animate_show()

    def animate_show(self):
        # Set initial state
        self.setWindowOpacity(0.0)
        
        # Get final position
        final_geo = self.geometry()
        
        # Create scaled down start position (center zoom)
        start_width = final_geo.width() * 0.8
        start_height = final_geo.height() * 0.8
        start_x = final_geo.x() + (final_geo.width() - start_width) // 2
        start_y = final_geo.y() + (final_geo.height() - start_height) // 2
        
        start_geo = QRect(int(start_x), int(start_y), int(start_width), int(start_height))
        
        # Start animations
        self.scale_animation.setStartValue(start_geo)
        self.scale_animation.setEndValue(final_geo)
        
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        
        self.scale_animation.start()
        self.fade_animation.start()

    def animate_close(self):
        # Fade out animation
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = 20
        self.close_btn.move(
            self.container.width() - self.close_btn.width() - margin,
            margin
        )
        self.close_btn.raise_()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.center().x() - self.width() // 2
        y = screen.center().y() - self.height() // 2
        self.move(x, y)

    def update_dropdown_style(self):
        BASE_DIR = Path(__file__).resolve().parents[3]
        ASSETS_DIR = BASE_DIR / "frontend" / "assets" / "images"
        arrow_path = ASSETS_DIR / "arrow_down.svg"

        if self.type_dropdown.currentIndex() == -1:
            self.type_dropdown.setStyleSheet(f"""
                QComboBox {{
                    font-family: 'Inter';
                    font-size: 12px;
                    font-weight: 600;
                    color: #777777;
                    font-style: italic;
                    padding: 5px 10px;
                    border: 1px solid #275D38;
                    border-radius: 1px;
                    background-color: #FFFFFF;
                    min-width: 180px;
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 24px;
                    background-color: #FFFFFF;
                }}
                QComboBox::down-arrow {{
                    image: url({arrow_path});
                    width: 12px;
                    height: 12px;
                }}
                QComboBox QAbstractItemView {{
                    border: 1px solid #275D38;
                    background-color: #FFFFFF;
                    outline: 0px;
                    border-radius: 1px;
                }}
                QComboBox QAbstractItemView::item {{
                    font-family: 'Roboto';
                    font-size: 14px;
                    font-weight: normal;
                    font-style: normal !important;
                    color: #275D38;
                    padding: 6px 10px;
                    text-align: center;
                    border-bottom: 1.5px solid #000000;
                    background-color: transparent;
                }}
                QComboBox QAbstractItemView::item:hover {{
                    background-color: #FDC601;
                    color: #000000;
                    font-weight: 200;
                }}
                QComboBox QAbstractItemView::item:selected {{
                    background-color: #FDC601;
                    color: #000000;
                    font-weight: 200;
                }}
            """)
        else:
            self.type_dropdown.setStyleSheet(f"""
                QComboBox {{
                    font-family: 'Roboto';
                    font-size: 12px;
                    font-weight: 600;
                    color: #275D38;
                    padding: 5px 10px;
                    border: 1px solid #275D38;
                    border-radius: 4px;
                    background-color: #FFFFFF;
                    min-width: 180px;
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 24px;
                    background-color: #FFFFFF;
                }}
                QComboBox::down-arrow {{
                    image: url({arrow_path});
                    width: 12px;
                    height: 12px;
                }}
                QComboBox QAbstractItemView {{
                    border: 1px solid #275D38;
                    background-color: #FFFFFF;
                    outline: 0px;
                    border-radius: 1px;
                }}
                QComboBox QAbstractItemView::item {{
                    font-family: 'Roboto';
                    font-size: 14px;
                    font-weight: normal;
                    color: #275D38;
                    padding: 6px 10px;
                    text-align: center;
                    border-bottom: 1.5px solid #000000;
                }}
                QComboBox QAbstractItemView::item:hover {{
                    background-color: #FDC601;
                    color: #000000;
                    font-weight: 200;
                }}
                QComboBox QAbstractItemView::item:selected {{
                    background-color: #FDC601;
                    color: #000000;
                    font-weight: 200;
                }}
            """)

    def show_success_popup(self):
        self.success_popup = MessageSentPopup()
        self.success_popup.show()
        self.success_popup.center_on_screen()

        QTimer.singleShot(2000, self.success_popup.close)
        QTimer.singleShot(2000, self.animate_close)

    def submit_feedback(self):
        """Collect form data and POST to the Django API endpoint."""
        submission_type = self.type_dropdown.currentText().lower() if self.type_dropdown.currentIndex() != -1 else None
        subject = self.subject_input.text().strip()
        message = self.message_input.toPlainText().strip()

        if not submission_type or not message:
            QMessageBox.warning(self, "Validation Error", "Please select a submission type and enter a message.")
            return

        payload = {
            "submission_type": submission_type,
            "subject": subject,
            "message": message,
            "is_anonymous": False,
        }

        API_BASE = "http://127.0.0.1:8000"
        url = f"{API_BASE}/api/feedback/"

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 201:
                    self.show_success_popup()
                else:
                    QMessageBox.critical(self, "Submission Error", f"Unexpected status code: {response.status}")
        
        except urllib.error.HTTPError as e:
            try:
                error_data = json.loads(e.read().decode('utf-8'))
                error_msg = str(error_data)
            except:
                error_msg = e.read().decode('utf-8')
            print(f"HTTP Error {e.code}: {error_msg}")
            QMessageBox.critical(self, "Submission Error", f"Error {e.code}: {error_msg}")
        except Exception as e:
            print(f"Connection Error: {str(e)}")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to server: {str(e)}")