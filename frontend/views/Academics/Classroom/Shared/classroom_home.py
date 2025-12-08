from PyQt6 import QtWidgets, QtCore, QtGui
from widgets.Academics.classroom_home_ui import Ui_ClassCard
from controller.Academics.Classroom.classroom_controller import ClassroomController

from frontend.controller.Academics.Tagging.classes_controller import ClassesController
from frontend.controller.Academics.controller_manager import ControllerManager


class ClassroomHome(QtWidgets.QWidget):
    class_selected = QtCore.pyqtSignal(dict)  # Signal to emit when a class is clicked

    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.controller = ClassroomController()

        manager = ControllerManager()
        controller = manager.get_classes_controller()
        # connect signals to automatically update home if Admin modifies classes in Tagging
        controller.class_created.connect(self.on_class_changed)
        controller.class_updated.connect(self.on_class_changed)
        controller.class_deleted.connect(self.on_class_changed)
        controller.class_archived.connect(self.on_class_changed)
        controller.class_unarchived.connect(self.on_class_changed)

        self.setup_ui()
        self.load_classes()

    def on_class_changed(self, data=None):
        """
        Called when admin creates/updates/deletes a class.
        Auto-refreshes the classroom home view.
        """
        print(f"[ClassroomHome] Detected class change, refreshing...")
        self.load_classes()

    def setup_ui(self):
        self.setMinimumSize(940, 530)
        self.setStyleSheet("background-color: white;")
        
        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(0)
        
        # Scroll area
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #F1F1F1;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #C1C1C1;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_content.setStyleSheet("background-color: white;")
        
        # Use QVBoxLayout for scroll content with stretch at the bottom
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        
        # Container for cards with grid layout
        self.cards_container = QtWidgets.QWidget()
        self.cards_container.setStyleSheet("background-color: white;")
        
        # Use Flow Layout (responsive) instead of GridLayout
        self.cards_layout = FlowLayout(self.cards_container, margin=10, spacing=20)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_layout.addWidget(self.cards_container)
        
        # Add stretch at bottom to push cards to top
        self.scroll_layout.addStretch(1)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)

    def load_classes(self):
        self.clear()

        classes = self.controller.get_classes()
        print(f"[ClassroomHome] Classes loaded: {classes}")

        for cls in classes:
            card_widget = QtWidgets.QFrame()
            card_ui = Ui_ClassCard()
            card_ui.setupUi(card_widget)
            
            # Set responsive size policy
            card_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Fixed
            )
            
            # Set card info with responsive font sizes
            card_ui.course_code_label.setText(cls['code'])
            card_ui.course_code_section_label.setText(cls.get('section_name', 'N/A'))
            card_ui.instructor_label.setText(cls['instructor'])
            
            # Make the entire card clickable
            card_widget.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            card_widget.mousePressEvent = lambda event, c=cls: self.class_selected.emit(c)

            self.cards_layout.addWidget(card_widget)

    def clear(self):
        # Clear all widgets from the flow layout
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def resizeEvent(self, event):
        """Handle window resize to adjust card sizes"""
        super().resizeEvent(event)
        
        # Update card sizes based on window width
        width = self.width()
        
        # Calculate card width based on window size
        if width < 800:
            # Small screens: 2 cards per row
            card_width = (width - 60) // 2
        elif width < 1200:
            # Medium screens: 3 cards per row
            card_width = (width - 80) // 3
        else:
            # Large screens: 4 cards per row
            card_width = (width - 100) // 4
            
        # Ensure minimum and maximum card width
        card_width = max(300, min(card_width, 400))
        
        # Update all cards
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                widget.setFixedWidth(card_width)
                
                # Adjust font sizes based on card width
                self.adjust_card_fonts(widget, card_width)

    def adjust_card_fonts(self, card_widget, card_width):
        """Adjust font sizes based on card width"""
        # Find child widgets
        course_code_label = card_widget.findChild(QtWidgets.QLabel, "course_code_label")
        section_label = card_widget.findChild(QtWidgets.QLabel, "course_code_section_label")
        instructor_label = card_widget.findChild(QtWidgets.QLabel, "instructor_label")
        
        # Adjust font sizes based on card width
        if card_width < 320:
            # Very small cards
            font_size_course = 20
            font_size_section = 12
            font_size_instructor = 11
        elif card_width < 360:
            # Small cards
            font_size_course = 22
            font_size_section = 13
            font_size_instructor = 12
        else:
            # Normal cards
            font_size_course = 24
            font_size_section = 14
            font_size_instructor = 13
        
        # Apply font sizes
        if course_code_label:
            course_code_label.setStyleSheet(f"""
                QLabel {{
                    color: rgba(255, 255, 255, 0.9);
                    font-size: {font_size_course}px;
                    font-weight: 600;
                    background: transparent;
                    font-family: "Poppins";
                }}
            """)
        
        if section_label:
            section_label.setStyleSheet(f"""
                QLabel {{
                    color: rgba(255, 255, 255, 0.9);
                    font-size: {font_size_section}px;
                    background: transparent;
                    font-family: "Poppins";
                }}
            """)
        
        if instructor_label:
            instructor_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    font-size: {font_size_instructor}px;
                    font-weight: 400;
                    font-family: "Poppins";
                    background: transparent;
                    margin-top: 4px;
                }}
            """)


class FlowLayout(QtWidgets.QLayout):
    """Custom flow layout for responsive card arrangement"""
    
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
            
        self.setSpacing(spacing)
        
        self.itemList = []
    
    def addItem(self, item):
        self.itemList.append(item)
    
    def count(self):
        return len(self.itemList)
    
    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None
    
    def expandingDirections(self):
        return QtCore.Qt.Orientation.Vertical
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        return self.doLayout(QtCore.QRect(0, 0, width, 0), True)
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()  # Fixed: Use minimumSize() method
    
    def minimumSize(self):
        size = QtCore.QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QtCore.QSize(2 * margin.left(), 2 * margin.top())
        return size
    
    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        
        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing()
            spaceY = self.spacing()
            nextX = x + item.sizeHint().width() + spaceX
            
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            
            if not testOnly:
                item.setGeometry(QtCore.QRect(x, y, item.sizeHint().width(), item.sizeHint().height()))
            
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
        
        return y + lineHeight - rect.y()
    
    
