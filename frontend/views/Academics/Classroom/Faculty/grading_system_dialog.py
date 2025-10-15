"""
Grading System Dialog Module
Handles the configuration of grading rubrics.
Integrated with the new table model architecture.
FIXED: Proper sizing and scrollable components
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QMessageBox, QLineEdit, QAbstractItemView, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtGui import QColor, QFont
from frontend.controller.Academics.Classroom.grading_system_controller import GradingSystemController


# ============================================================================
# DATA MODEL LAYER (from original file)
# ============================================================================

class ComponentItem:
    """Represents a single grading component"""
    def __init__(self, name: str, percentage: int, component_id: int = None):
        self.id = component_id
        self.name = name
        self.percentage = percentage
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'percentage': self.percentage
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get('name', ''),
            percentage=data.get('percentage', 0),
            component_id=data.get('id')
        )


class TermRubric:
    """Represents rubric for a single term"""
    def __init__(self, term_name: str, term_percentage: int):
        self.term_name = term_name
        self.term_percentage = term_percentage
        self.components = []
    
    def add_component(self, component: ComponentItem):
        self.components.append(component)
    
    def remove_component(self, index: int):
        if 0 <= index < len(self.components):
            del self.components[index]
    
    def update_component(self, index: int, name: str, percentage: int):
        if 0 <= index < len(self.components):
            self.components[index].name = name
            self.components[index].percentage = percentage
    
    def get_total_percentage(self):
        return sum(c.percentage for c in self.components)
    
    def is_valid(self):
        return self.get_total_percentage() == 100
    
    def to_dict(self):
        return {
            'term_name': self.term_name,
            'term_percentage': self.term_percentage,
            'components': [c.to_dict() for c in self.components]
        }
    
    @classmethod
    def from_dict(cls, data):
        rubric = cls(
            term_name=data.get('term_name', ''),
            term_percentage=data.get('term_percentage', 0)
        )
        for comp_data in data.get('components', []):
            rubric.add_component(ComponentItem.from_dict(comp_data))
        return rubric


class GradingSystemModel(QObject):
    """Main model for the grading system"""
    data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.midterm_rubric = TermRubric("Midterm", 33)
        self.final_rubric = TermRubric("Final", 67)
        self.load_default_rubrics()
    
    def load_default_rubrics(self):
        self.midterm_rubric.add_component(ComponentItem("Performance Task", 20))
        self.midterm_rubric.add_component(ComponentItem("Quiz", 30))
        self.midterm_rubric.add_component(ComponentItem("Exam", 50))
        
        self.final_rubric.add_component(ComponentItem("Performance Task", 20))
        self.final_rubric.add_component(ComponentItem("Quiz", 30))
        self.final_rubric.add_component(ComponentItem("Exam", 50))
    
    def get_rubric(self, term: str):
        if term.lower() == "midterm":
            return self.midterm_rubric
        elif term.lower() == "final":
            return self.final_rubric
        return None
    
    def validate_all(self):
        return (self.midterm_rubric.is_valid() and 
                self.final_rubric.is_valid())
    
    def to_dict(self):
        return {
            'midterm': self.midterm_rubric.to_dict(),
            'final': self.final_rubric.to_dict()
        }


# ============================================================================
# VIEW LAYER - COMPONENTS
# ============================================================================

class TermRubricWidget(QWidget):
    """Widget displaying rubric table for a single term - FIXED: Better sizing"""
    
    def __init__(self, term_name: str, term_percentage: int, 
                 controller: GradingSystemController, parent=None):
        super().__init__(parent)
        self.term_name = term_name
        self.term_percentage = term_percentage
        self.controller = controller
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 15)
        layout.setSpacing(8)
        
        # Term header
        term_header = QLabel(f"{self.term_name}: {self.term_percentage}%")
        term_header.setStyleSheet("""
            QLabel {
                color: #084924;
                font-size: 14px;
                font-weight: bold;
                padding: 5px 0px;
            }
        """)
        layout.addWidget(term_header)
        
        # Components table - FIXED: Set proper height
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["No", "Component", "Percentage"])
        self.table.setMinimumHeight(150)  # FIXED: Minimum height
        self.table.setMaximumHeight(200)  # FIXED: Maximum height
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                gridline-color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
                color: #000000;
            }
            QTableWidget::item:selected {
                background-color: #E8F5E8;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #084924;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 11px;
                border: none;
                border-right: 1px solid #0A5A2A;
            }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        
        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.add_button = QPushButton("+ Add")
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #FDC601;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #E5B200;
            }
        """)
        self.add_button.clicked.connect(self.add_component)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #999999;
            }
        """)
        self.delete_button.clicked.connect(self.delete_component)
        self.delete_button.setEnabled(False)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        
        self.total_label = QLabel("Total: 0%")
        self.total_label.setStyleSheet("""
            QLabel {
                color: #084924;
                font-weight: bold;
                font-size: 12px;
                padding: 5px 10px;
            }
        """)
        button_layout.addWidget(self.total_label)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    @pyqtSlot()
    def on_selection_changed(self):
        has_selection = len(self.table.selectedItems()) > 0
        self.delete_button.setEnabled(has_selection)
    
    def load_data(self, rubric: TermRubric):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        for i, component in enumerate(rubric.components):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, num_item)
            
            name_item = QTableWidgetItem(component.name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, name_item)
            
            pct_item = QTableWidgetItem(f"{component.percentage}%")
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, pct_item)
        
        self.update_total()
        self.table.blockSignals(False)
    
    @pyqtSlot(int, int)
    def on_cell_changed(self, row, column):
        if column == 1:
            name = self.table.item(row, 1).text()
            pct_text = self.table.item(row, 2).text().replace('%', '').strip()
            try:
                percentage = int(pct_text)
                self.controller.update_component(
                    self.term_name.lower(),
                    row,
                    name,
                    percentage
                )
            except (ValueError, AttributeError):
                pass
        elif column == 2:
            pct_text = self.table.item(row, 2).text().replace('%', '').strip()
            try:
                percentage = int(pct_text)
                name = self.table.item(row, 1).text()
                self.controller.update_component(
                    self.term_name.lower(),
                    row,
                    name,
                    percentage
                )
                self.table.blockSignals(True)
                self.table.item(row, 2).setText(f"{percentage}%")
                self.table.blockSignals(False)
                self.update_total()
            except (ValueError, AttributeError):
                rubric = self.controller.model.get_rubric(self.term_name.lower())
                if rubric and row < len(rubric.components):
                    self.table.blockSignals(True)
                    self.table.item(row, 2).setText(f"{rubric.components[row].percentage}%")
                    self.table.blockSignals(False)
    
    @pyqtSlot()
    def add_component(self):
        self.controller.add_component(self.term_name.lower(), "New Component", 0)
        rubric = self.controller.model.get_rubric(self.term_name.lower())
        if rubric:
            self.load_data(rubric)
    
    @pyqtSlot()
    def delete_component(self):
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if selected_rows:
            row = min(selected_rows)
            self.controller.remove_component(self.term_name.lower(), row)
            rubric = self.controller.model.get_rubric(self.term_name.lower())
            if rubric:
                self.load_data(rubric)
    
    def update_total(self):
        rubric = self.controller.model.get_rubric(self.term_name.lower())
        if rubric:
            total = rubric.get_total_percentage()
            color = "#084924" if total == 100 else "#DC3545"
            self.total_label.setText(f"Total: {total}%")
            self.total_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-weight: bold;
                    font-size: 12px;
                    padding: 5px 10px;
                }}
            """)


# ============================================================================
# MAIN DIALOG - FIXED SIZING
# ============================================================================

class GradingSystemDialog(QDialog):
    """Main dialog for configuring the grading system - FIXED: Proper sizing and scrolling"""
    rubric_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = GradingSystemModel()
        self.controller = GradingSystemController(self.model)
        self.setup_ui()
        self.connect_signals()
        self.load_initial_data()
    
    def setup_ui(self):
        self.setWindowTitle("Grading System")
        self.setModal(True)
        
        # FIXED: Better sizing that works with parent window
        self.setMinimumSize(600, 600)
        self.setMaximumSize(800, 900)
        self.resize(650, 700)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)
        
        # Header
        header = QLabel("Grading System")
        header.setStyleSheet("""
            QLabel {
                color: #084924;
                font-size: 20px;
                font-weight: bold;
                padding-bottom: 10px;
            }
        """)
        main_layout.addWidget(header)
        
        # FIXED: Create scrollable area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #F0F0F0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9E9E9E;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(20)
        
        # Add rubric widgets to content
        self.midterm_widget = TermRubricWidget("Midterm", 33, self.controller)
        content_layout.addWidget(self.midterm_widget)
        
        self.final_widget = TermRubricWidget("Final", 67, self.controller)
        content_layout.addWidget(self.final_widget)
        
        content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Button layout at bottom (fixed, not scrolling)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #084924;
                border: 2px solid #084924;
                border-radius: 5px;
                padding: 10px 30px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #F0F8F0;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("Save")
        self.save_button.setFixedHeight(40)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0A5A2A;
            }
        """)
        self.save_button.clicked.connect(self.save_rubric)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
    
    def connect_signals(self):
        self.controller.validation_error.connect(self.show_validation_error)
        self.controller.save_success.connect(self.on_save_success)
        self.model.data_changed.connect(self.refresh_displays)
    
    def load_initial_data(self):
        self.midterm_widget.load_data(self.model.midterm_rubric)
        self.final_widget.load_data(self.model.final_rubric)
    
    @pyqtSlot()
    def refresh_displays(self):
        self.midterm_widget.update_total()
        self.final_widget.update_total()
    
    @pyqtSlot()
    def save_rubric(self):
        if self.controller.validate_and_save():
            self.rubric_saved.emit(self.model.to_dict())
            self.accept()
    
    @pyqtSlot(str)
    def show_validation_error(self, message: str):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Validation Error")
        msg_box.setText("Cannot save grading system")
        msg_box.setInformativeText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 20px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #0A5A2A;
            }
        """)
        msg_box.exec()
    
    @pyqtSlot()
    def on_save_success(self):
        pass


# ============================================================================
# INTEGRATION FUNCTIONS
# ============================================================================

def show_grading_dialog(parent_window):
    """Show the grading system dialog"""
    dialog = GradingSystemDialog(parent_window)
    dialog.rubric_saved.connect(lambda data: on_rubric_saved(parent_window, data))
    result = dialog.exec()
    return dialog


def on_rubric_saved(main_window, rubric_data):
    """Handle when rubric is saved - integrate with main app"""
    print("=" * 60)
    print("RUBRIC SAVED SUCCESSFULLY")
    print("=" * 60)
    
    if hasattr(main_window, 'grade_model'):
        # Update the grade model with new rubric configuration
        main_window.grade_model.update_rubric_config(rubric_data)
        
        # Trigger table rebuild through controller
        # This will cause columns_changed signal to emit
        print("[INFO] Table will rebuild with new rubric configuration")


def connect_grading_button(main_window, grading_label):
    """
    Make the grading system label/button clickable.
    
    Usage in MainWindow.__init__:
        connect_grading_button(self, self.grading_label)
    """
    def on_label_click(event):
        show_grading_dialog(main_window)
    
    grading_label.mousePressEvent = on_label_click
    grading_label.setCursor(Qt.CursorShape.PointingHandCursor)