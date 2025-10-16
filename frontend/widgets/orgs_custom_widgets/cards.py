from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainterPath, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
import os

STYLE_GREEN_BTN = "background-color: #084924; color: white; border-radius: 5px; padding-top: 10px;padding-bottom: 10px; font-weight: bold;"
STYLE_RED_BTN = "background-color: #EB5757; color: white; border-radius: 5px;"
STYLE_PRIMARY_BTN = "background-color: #084924; color: white; border-radius: 5px;"
STYLE_YELLOW_BTN = "background-color: #FDC601; color: white; border-radius: 5px; padding-top: 10px;padding-bottom: 10px; font-weight: bold;"

def create_rounded_pixmap(source_pixmap, radius=10):
    size = source_pixmap.size()
    rounded = QPixmap(size)
    rounded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, source_pixmap)
    painter.end()
    return rounded

def resolve_image_path(relative_path):
    """Resolve relative image path to absolute path in Data folder."""
    if relative_path == "No Photo" or not relative_path:
        return "No Photo"
    
    # If it's already an absolute path that exists, return it
    if os.path.isabs(relative_path) and os.path.exists(relative_path):
        return relative_path
    
    # Resolve from Data folder
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(base_dir, "views", "Organizations", "Data", relative_path)
    
    if os.path.exists(data_path):
        return data_path
    
    # Fallback to relative path
    return relative_path

class JoinedOrgCard(QtWidgets.QFrame):
    def __init__(self, logo_path, org_data, main_window):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        self.setStyleSheet("""
            QFrame {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 10px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)

        logo_label = QtWidgets.QLabel()
        logo_label.setMaximumSize(200, 200)
        logo_label.setMinimumSize(200, 200)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        logo_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        logo_label.setStyleSheet("border: none; background-color: transparent;")

        resolved_logo_path = resolve_image_path(logo_path)
        
        if resolved_logo_path != "No Photo":
            pixmap = QPixmap(resolved_logo_path).scaled(200, 200, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            if not pixmap.isNull():
                rounded_pixmap = create_rounded_pixmap(pixmap, 10)
                logo_label.setPixmap(rounded_pixmap)
            else:
                logo_label.setText("No Logo")
        else:
            logo_label.setText("No Logo")

        btn_details = QtWidgets.QPushButton("More Details")
        btn_details.setStyleSheet(STYLE_YELLOW_BTN)
        btn_details.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        btn_details.clicked.connect(lambda: main_window.show_org_details(org_data))

        layout.addWidget(logo_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(btn_details)

class CollegeOrgCard(QtWidgets.QFrame):
    def __init__(self, logo_path, description, org_data, main_window):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        self.setStyleSheet("""
            QFrame {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 10px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignHCenter)

        logo_label = QtWidgets.QLabel()
        logo_label.setMaximumSize(200, 200)
        logo_label.setMinimumSize(200, 200)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignHCenter)
        logo_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        logo_label.setStyleSheet("border: none; background-color: transparent;")

        resolved_logo_path = resolve_image_path(logo_path)
        
        if resolved_logo_path != "No Photo":
            pixmap = QPixmap(resolved_logo_path).scaled(200, 200, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            if not pixmap.isNull():
                rounded_pixmap = create_rounded_pixmap(pixmap, 10)
                logo_label.setPixmap(rounded_pixmap)
            else:
                logo_label.setText("No Logo")
        else:
            logo_label.setText("No Logo")

        desc_label = QtWidgets.QLabel()
        desc_label.setStyleSheet("border: none; background-color: transparent; font-weight: bold;")
        
        desc_label.setMaximumHeight(16)
        
        desc_label.setText(description)
        desc_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        desc_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        desc_label.setWordWrap(True)

        btn_details = QtWidgets.QPushButton("More Details")
        btn_apply = QtWidgets.QPushButton("Apply")
        btn_details.setStyleSheet(STYLE_YELLOW_BTN)
        btn_apply.setStyleSheet(STYLE_GREEN_BTN)
        btn_details.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        btn_apply.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        btn_details.clicked.connect(lambda: main_window.show_org_details(org_data))

        layout.addWidget(logo_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(desc_label)
        layout.addWidget(btn_details)
        layout.addWidget(btn_apply)

class OfficerCard(QtWidgets.QFrame):
    def __init__(self, officer_data, main_window):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        self.setStyleSheet("""
            QFrame {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 10px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        top_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(top_spacer)

        image_label = QtWidgets.QLabel()
        image_label.setFixedSize(150, 150)
        image_label.setStyleSheet("border: none; ")
        image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)

        if "card_image_path" in officer_data and officer_data["card_image_path"] != "No Photo":
            resolved_image_path = resolve_image_path(officer_data["card_image_path"])
            pixmap = QPixmap(resolved_image_path).scaled(150, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            if not pixmap.isNull():
                image_label.setPixmap(pixmap)
            else:
                image_label.setText("No Image")
        else:
            image_label.setText("No Image")

        name_label = QtWidgets.QLabel(officer_data.get("name", "Unknown"))
        name_label.setStyleSheet("border: none; font-weight: bold;")
        name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        position_label = QtWidgets.QLabel(officer_data.get("position", "Unknown Position"))
        position_label.setStyleSheet("border: none;")
        position_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        btn_details = QtWidgets.QPushButton("Officer Details")
        btn_details.setStyleSheet("background-color: #FFD700; color: black; border-radius: 5px; font-weight: bold;")
        btn_details.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        btn_details.clicked.connect(lambda: main_window.show_officer_dialog(officer_data))

        layout.addWidget(image_label)
        layout.addWidget(name_label)
        layout.addWidget(position_label)
        layout.addWidget(btn_details)

        bottom_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(bottom_spacer)

class EventCard(QtWidgets.QFrame):
    def __init__(self, event_data, main_window):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(125)
        self.setMinimumWidth(65)
        self.setStyleSheet("""
            QFrame {
                color: #084924;
                background-color: #fff;
                border: 1px solid #084924;
                border-radius: 10px;
            }
        """)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        empty_btn = QtWidgets.QPushButton()
        empty_btn.setStyleSheet("""background-color: #084924;
                                color: white;
                                border: 3px solid #084924;
                                font-weight: bold; 
                                border-top-right-radius: 8px;
                                border-top-left-radius: 8px;
                                border-bottom-right-radius: 0px;
                                border-bottom-left-radius: 0px;
                                """)
        empty_btn.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        main_layout.addWidget(empty_btn)

        header = QtWidgets.QFrame(self)
        header_layout = QtWidgets.QHBoxLayout(header)
        header.setStyleSheet("background-color: transparent; border: none;")
        header_layout.setContentsMargins(10, 5, 10, 5) 

        header_group = QtWidgets.QWidget()
        group_layout = QtWidgets.QHBoxLayout(header_group)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(0)

        name_label = QtWidgets.QLabel(event_data.get("name", "Unknown Event"))
        name_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        date_label = QtWidgets.QLabel(event_data.get("date", "No Date"))

        group_layout.addWidget(name_label)
        
        group_layout.addItem(QtWidgets.QSpacerItem(15, 0, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed))
        
        group_layout.addWidget(date_label)
        
        header_layout.addStretch(1) 
        
        header_layout.addWidget(header_group) 
        
        header_layout.addStretch(1) 

        main_layout.addWidget(header)

        content_label = QtWidgets.QLabel(event_data.get("description", "No Description"))
        content_label.setStyleSheet("padding: 10px; font-size: 12px; border: none;")
        content_label.setWordWrap(True)
        content_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(content_label)
