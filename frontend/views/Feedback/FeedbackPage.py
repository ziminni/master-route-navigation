import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QTextEdit,
    QPushButton, QHBoxLayout, QFrame, QStyledItemDelegate, QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
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
        self.setFixedSize(500, 400)  # Reduced from 740x620
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 3px solid #084924;
                border-radius: 12px;  /* Reduced from 16px */
            }
        """)
        container.setObjectName("container")
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setContentsMargins(60, 60, 60, 60)  # Reduced from 100

        # Image path
        BASE_DIR = Path(__file__).resolve().parents[3]  # [proj name]
        ASSETS_DIR = BASE_DIR / "frontend" / "assets" / "images"
        smile_path = ASSETS_DIR / "smile.svg"

        icon_widget = QSvgWidget(str(smile_path))
        icon_widget.setFixedSize(100, 100)  # Reduced from 150x150
        icon_widget.setStyleSheet("background: transparent;")
        container_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        message_label = QLabel("Message sent!")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            font-size: 40px;  /* Reduced from 60px */
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
            font-size: 16px;  /* Reduced from 19px */
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
        self.setFixedSize(800, 600)  # Reduced from 1075x750
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setStyleSheet("background-color: transparent;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 3px solid #0b3d0b;
                border-radius: 12px;  /* Reduced from 16px */
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 20)  # Reduced from 40,30,40,30
        layout.setSpacing(15)  # Reduced from 20

        header = QHBoxLayout()
        header.setContentsMargins(0, 30, 0, 0)  # Reduced from 0,40,0,0

        header.addStretch()

        title = QLabel("SUGGESTION, COMPLAINT, & FEEDBACK BOX")
        title.setStyleSheet("""
            QLabel {
                font-family: 'Poppins';
                font-size: 32px;  /* Reduced from 43px */
                font-weight: 1000;
                color: rgba(8, 73, 36, 204);
                border: none;
                background-color: transparent;
            }
        """)
        title.setFixedHeight(40)  # Reduced from 50
        title_font = title.font()
        title_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 91)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)

        header.addStretch()
        layout.addLayout(header)
        layout.addSpacing(15)  # Reduced from 20

        close_btn = QPushButton("✕", container)
        close_btn.setFixedSize(30, 30)  # Reduced from 40x40
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #036800;
                color: white;
                font-size: 14px;  /* Reduced from 18px */
                border-radius: 15px;  /* Reduced from 20px */
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #124d12;
            }
        """)
        close_btn.clicked.connect(self.close)
        self.close_btn = close_btn
        self.container = container

        type_row = QHBoxLayout()
        type_row.setSpacing(5)  # Reduced from 7
        type_label = QLabel("Type:")
        type_label.setStyleSheet("""
            font-family: 'Inter';
            font-size: 14px;  /* Reduced from 18px */
            font-weight: 600;
            color: #333333;
            border: none;
        """)
        type_row.addWidget(type_label)

        self.type_dropdown = QComboBox()
        self.type_dropdown.addItems(["Suggestion", "Complaint", "Feedback"])
        self.type_dropdown.setCurrentIndex(-1)  # placeholder
        self.type_dropdown.setPlaceholderText("Submission Type")
        self.type_dropdown.setItemDelegate(CenterDelegate(self.type_dropdown))
        self.type_dropdown.currentIndexChanged.connect(self.update_dropdown_style)
        self.update_dropdown_style()
        type_row.addWidget(self.type_dropdown)
        type_row.addStretch()
        layout.addLayout(type_row)

        subject = QLineEdit()
        subject.setFixedHeight(50)  # Reduced from 70
        subject.setStyleSheet("""
            font-family: 'Inter';
            font-size: 14px;  /* Reduced from 16px */
            padding: 8px;  /* Reduced from 10px */
            border: 1px solid #275D38;
            border-radius: 10px;  /* Reduced from 12px */
        """)
        layout.addWidget(subject)

        message = QTextEdit()
        message.setFixedHeight(250)  # Reduced from 330
        message.setStyleSheet("""
            font-family: 'Inter';
            font-size: 14px;  /* Reduced from 16px */
            padding: 8px;  /* Reduced from 10px */
            border: 1px solid #275D38;
            border-radius: 10px;  /* Reduced from 12px */
        """)
        layout.addWidget(message)

        submit_btn = QPushButton("SUBMIT MESSAGE")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                font-family: 'Inter';
                font-size: 14px;  /* Reduced from 16px */
                font-weight: 700;
                padding: 12px 60px;  /* Reduced from 16px 80px */
                border-radius: 6px;  /* Reduced from 8px */
                border: none;
            }
            QPushButton:hover {
                background-color: #0a5529;
            }
        """)
        submit_btn.clicked.connect(self.show_success_popup)
        layout.addWidget(submit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(container)
        self.center_on_screen()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = 20  # Reduced from 25
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
        # Image path
        BASE_DIR = Path(__file__).resolve().parents[3]  # [proj name]
        ASSETS_DIR = BASE_DIR / "frontend" / "assets" / "images"
        arrow_path = ASSETS_DIR / "arrow_down.svg"

        if self.type_dropdown.currentIndex() == -1:
            self.type_dropdown.setStyleSheet(f"""
                QComboBox {{
                    font-family: 'Inter';
                    font-size: 12px;  /* Reduced from 14px */
                    font-weight: 600;
                    color: #777777;
                    font-style: italic;
                    padding: 5px 10px;  /* Reduced from 6px 12px */
                    border: 1px solid #275D38;
                    border-radius: 1px;
                    background-color: #FFFFFF;
                    min-width: 180px;  /* Reduced from 220px */
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 24px;  /* Reduced from 28px */
                    background-color: #FFFFFF;
                }}
                QComboBox::down-arrow {{
                    image: url({arrow_path});
                    width: 12px;  /* Reduced from 14px */
                    height: 12px;  /* Reduced from 14px */
                }}
                QComboBox QAbstractItemView {{
                    border: 1px solid #275D38;
                    background-color: #FFFFFF;
                    outline: 0px;
                    border-radius: 1px;
                }}
                QComboBox QAbstractItemView::item {{
                    font-family: 'Roboto';
                    font-size: 14px;  /* Reduced from 16px */
                    font-weight: normal;
                    font-style: normal !important;
                    color: #275D38;
                    padding: 6px 10px;  /* Reduced from 8px 12px */
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
                    font-size: 12px;  /* Reduced from 14px */
                    font-weight: 600;
                    color: #275D38;
                    padding: 5px 10px;  /* Reduced from 6px 12px */
                    border: 1px solid #275D38;
                    border-radius: 4px;
                    background-color: #FFFFFF;
                    min-width: 180px;  /* Reduced from 220px */
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 24px;  /* Reduced from 28px */
                    background-color: #FFFFFF;
                }}
                QComboBox::down-arrow {{
                    image: url({arrow_path});
                    width: 12px;  /* Reduced from 14px */
                    height: 12px;  /* Reduced from 14px */
                }}
                QComboBox QAbstractItemView {{
                    border: 1px solid #275D38;
                    background-color: #FFFFFF;
                    outline: 0px;
                    border-radius: 1px;
                }}
                QComboBox QAbstractItemView::item {{
                    font-family: 'Roboto';
                    font-size: 14px;  /* Reduced from 16px */
                    font-weight: normal;
                    color: #275D38;
                    padding: 6px 10px;  /* Reduced from 8px 12px */
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

        # Autoclose both popups after 2 seconds
        QTimer.singleShot(2000, self.success_popup.close)
        QTimer.singleShot(2000, self.close)