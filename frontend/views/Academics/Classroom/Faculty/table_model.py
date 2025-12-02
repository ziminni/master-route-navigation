"""
Custom QAbstractTableModel implementation with:
- Bulk input support in headers (TRULY FIXED: uses viewport as parent)
- Draft/upload status for grades with three-dot menu in cells
- Expandable column headers with dynamic colors
- Component aggregation display
- Proper expand/collapse indicators
"""
import os
import sys

# Navigate 5 levels up to get to the project's root directory (MAIN_MODULE2)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

# Add the project root to the system path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.services.Academics.model.Academics.Classroom.grades_table_model import GradesTableModel # noqa: E402

from PyQt6.QtWidgets import (
    QTableView, QHeaderView, QStyledItemDelegate, QLineEdit,
    QWidget, QHBoxLayout, QMenu, QToolButton, QLabel, QStyle 
)
from PyQt6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, pyqtSignal, QVariant, QPoint, QRect
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QAction


class BulkInputHeaderView(QHeaderView):
    """
    Custom header with:
    - Expandable indicators (right arrow collapsed, down arrow expanded)
    - Bulk input widgets (parented to viewport for proper scrolling)
    - Draft/upload options menu
    - Dynamic colors based on expand state
    """
    
    section_expand_clicked = pyqtSignal(int, dict)  # section, column_info
    bulk_input_changed = pyqtSignal(int, str)  # column, value
    upload_column_clicked = pyqtSignal(int)  # column
    draft_column_clicked = pyqtSignal(int)  # column
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bulk_widgets = {}  # {column: widget}
        self.sectionClicked.connect(self._on_section_clicked)
        self.expanded_main_column = None  # Track which main column is expanded
        self.expanded_states = {}  # Track all expansion states
        
        # CRITICAL: Connect to geometry changes
        self.sectionResized.connect(self._on_section_resized)
        
    def set_expanded_states(self, expanded_main, all_states):
        """Set expanded states for dynamic coloring"""
        self.expanded_main_column = expanded_main
        self.expanded_states = all_states
        self.viewport().update()
    
    def _on_section_clicked(self, logical_index):
        """Handle section click for expandable columns"""
        model = self.model()
        if not model:
            return
        
        col_info = model.headerData(logical_index, Qt.Orientation.Horizontal, 
                                     GradesTableModel.ColumnInfoRole)
        
        if col_info and col_info.get('type') in ['expandable_main', 'expandable_component']:
            self.section_expand_clicked.emit(logical_index, col_info)
    
    def _on_section_resized(self, logicalIndex, oldSize, newSize):
        """Handle section resize - reposition widget if it exists"""
        if logicalIndex in self.bulk_widgets:
            self._position_bulk_widget(logicalIndex)
    
    def _is_expanded(self, col_info):
        """Check if a column is expanded"""
        col_type = col_info.get('type', '')
        
        if col_type == 'expandable_main':
            target = col_info.get('target', '')
            if target == 'midterm':
                return self.expanded_states.get('midterm_expanded', False)
            elif target == 'finalterm':
                return self.expanded_states.get('finalterm_expanded', False)
        
        elif col_type == 'expandable_component':
            component = col_info.get('component', '')
            term = col_info.get('term', '')
            state_key = f'{component}_{term}_expanded'
            return self.expanded_states.get(state_key, False)
        
        return False
    
    def _get_header_color(self, col_info, col_type):
        """Get header background color based on expand state"""
        if self.expanded_main_column:
            col_term = col_info.get('term', '')
            col_target = col_info.get('target', '')
            
            if (col_target == self.expanded_main_column or 
                col_term == self.expanded_main_column):
                return QColor("#036800")
        
        return QColor("#084924")
    
    def _get_text_color(self, col_info, col_type):
        """Get text color based on column type and expand state"""
        if self.expanded_main_column:
            col_term = col_info.get('term', '')
            col_target = col_info.get('target', '')
            
            if col_type == 'expandable_main' and col_target == self.expanded_main_column:
                return QColor("white")
            
            if col_type == 'expandable_component' and col_term == self.expanded_main_column:
                return QColor("#FFC000")
            
            if col_type == 'grade_input' and col_term == self.expanded_main_column:
                return QColor("#FFC000")
        
        return QColor("white")
    
    def paintSection(self, painter, rect, logicalIndex):
        """Custom paint for header sections with dynamic colors"""
        model = self.model()
        if not model:
            super().paintSection(painter, rect, logicalIndex)
            return
        
        col_info = model.headerData(logicalIndex, Qt.Orientation.Horizontal,
                                     GradesTableModel.ColumnInfoRole)
        
        if not col_info:
            super().paintSection(painter, rect, logicalIndex)
            return
        
        col_type = col_info.get('type', '')
        
        # Draw Background Color (DYNAMIC)
        bg_color = self._get_header_color(col_info, col_type)
        painter.fillRect(rect, bg_color)
        
        # Draw Border
        painter.setPen(QPen(QColor("#0A5A2A"), 1))
        painter.drawLine(rect.topRight(), rect.bottomRight())
        
        # Setup Text Drawing (DYNAMIC COLOR)
        text_color = self._get_text_color(col_info, col_type)
        painter.setPen(text_color)
        
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        # Get the text to display
        text = model.headerData(logicalIndex, Qt.Orientation.Horizontal, 
                                Qt.ItemDataRole.DisplayRole)
        
        # Calculate Text Rectangle
        if col_type == 'grade_input':
            text_rect = rect.adjusted(8, 5, -8, -30)
            text_alignment = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop
            
        elif col_type in ['expandable_main', 'expandable_component']:
            text_rect = rect.adjusted(8, 5, -25, -5)
            text_alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            
        else:
            text_rect = rect.adjusted(8, 5, -8, -5)
            
            if logicalIndex == 0 or 'Final Grade' in str(text):
                text_alignment = Qt.AlignmentFlag.AlignCenter
            else:
                text_alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        # Draw the Text with Word Wrap
        painter.drawText(
            text_rect,
            text_alignment | Qt.TextFlag.TextWordWrap,
            str(text) if text else ""
        )
        
        # Draw Expand Indicator
        if col_type in ['expandable_main', 'expandable_component']:
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            indicator_rect = rect.adjusted(rect.width() - 20, 0, -5, 0)
            
            is_expanded = self._is_expanded(col_info)
            arrow = "▼" if is_expanded else "▶"
            
            painter.drawText(
                indicator_rect,
                Qt.AlignmentFlag.AlignCenter,
                arrow
            )
    
        # In the BulkInputHeaderView class, update the create_bulk_widget method:
    def create_bulk_widget(self, column, max_score=40):
        """Create bulk input widget for a grade column - parented to viewport()"""
        container = QWidget(self.viewport())
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # Input field
        input_field = QLineEdit()
        input_field.setPlaceholderText("__")
        input_field.setMaximumWidth(45)
        input_field.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        input_field.textChanged.connect(
            lambda text, col=column: self._on_bulk_input_changed(col, text, max_score)
        )
        
        # "out of" label
        out_of_label = QLabel(f"/{max_score}")
        out_of_label.setStyleSheet("color: white; font-size: 11px; font-weight: bold;")
        
        # Options button (three dots)
        options_btn = QToolButton()
        options_btn.setText("⋯")
        options_btn.setFixedSize(20, 20)
        options_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color:  #023020;
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
            }
            QToolButton:hover {
                background: rgba(255,255,255,0.2);
                border-radius: 3px;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        
        menu = QMenu(options_btn)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #E8F5E8;
            }
        """)
        
        # FIXED: Pass column index properly
        draft_action = menu.addAction("Keep as Draft")
        draft_action.triggered.connect(lambda checked=False, col=column: self.draft_column_clicked.emit(col))
        
        upload_action = menu.addAction("Upload All")
        upload_action.triggered.connect(lambda checked=False, col=column: self.upload_column_clicked.emit(col))
        
        options_btn.setMenu(menu)
        options_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        layout.addWidget(input_field)
        layout.addWidget(out_of_label)
        layout.addStretch()
        layout.addWidget(options_btn)
        
        return container
    
    def _position_bulk_widget(self, column):
        """Position a single bulk widget - uses sectionViewportPosition for viewport parent"""
        if column not in self.bulk_widgets:
            return
        
        widget = self.bulk_widgets[column]
        
        # CRITICAL: Use sectionViewportPosition since widget is parented to viewport
        x_pos = self.sectionViewportPosition(column)
        width = self.sectionSize(column)
        
        widget.setGeometry(
            x_pos,
            self.height() - 28,
            width,
            25
        )
    
    def reposition_all_bulk_widgets(self):
        """Reposition all bulk widgets"""
        for column in self.bulk_widgets.keys():
            self._position_bulk_widget(column)
    
    def _on_bulk_input_changed(self, column, text, max_score):
        """Handle bulk input change"""
        if text:
            value = f"{text}/{max_score}"
            self.bulk_input_changed.emit(column, value)


class CellOptionsWidget(QWidget):
    """Three-dot menu widget that appears in each grade cell"""
    
    upload_requested = pyqtSignal()
    keep_draft_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(0)
        
        self.options_btn = QToolButton()
        self.options_btn.setText("⋯")
        self.options_btn.setFixedSize(16, 16)
        self.options_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #666;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }
            QToolButton:hover {
                background: rgba(0,0,0,0.1);
                border-radius: 2px;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        
        menu = QMenu(self.options_btn)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #E8F5E8;
            }
        """)
        
        draft_action = menu.addAction("Keep as Draft")
        draft_action.triggered.connect(self.keep_draft_requested.emit)
        
        upload_action = menu.addAction("Upload")
        upload_action.triggered.connect(self.upload_requested.emit)
        
        self.options_btn.setMenu(menu)
        self.options_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        layout.addStretch()
        layout.addWidget(self.options_btn)


class GradeInputDelegate(QStyledItemDelegate):
    """Custom delegate for grade input cells with integrated options menu"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.option_widgets = {}
    
    def paint(self, painter, option, index):
        """Custom paint to show cell with options button"""
        super().paint(painter, option, index)
    
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setPlaceholderText("e.g., 35/40")
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return editor
    
    def setEditorData(self, editor, index):
        value = index.data(Qt.ItemDataRole.EditRole)
        editor.setText(str(value) if value else "")
    
    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, value, Qt.ItemDataRole.EditRole)


class EnhancedGradesTableView(QTableView):
    """
    Main table view with all features integrated
    ULTIMATE FIX: Bulk widgets parented to header viewport for automatic scroll handling
    """
    
    def __init__(self, data_model, controller, parent=None):
        super().__init__(parent)
        
        self.data_model = data_model
        self.controller = controller
        self.cell_option_widgets = {}
        
        # Setup model
        self.table_model = GradesTableModel(data_model, controller)
        self.setModel(self.table_model)
        
        # Setup custom header
        self.custom_header = BulkInputHeaderView(Qt.Orientation.Horizontal, self)
        self.setHorizontalHeader(self.custom_header)
        
        # Setup delegate
        self.delegate = GradeInputDelegate(self)
        self.setItemDelegate(self.delegate)
        
        # Connect signals
        self.custom_header.section_expand_clicked.connect(self._on_header_expand)
        self.custom_header.bulk_input_changed.connect(self._on_bulk_input)
        self.custom_header.upload_column_clicked.connect(self._on_upload_column)
        self.custom_header.draft_column_clicked.connect(self._on_draft_column)
        self.data_model.columns_changed.connect(self._update_header_colors)
        self.table_model.dataChanged.connect(self._on_data_changed)
        
        # Table appearance settings
        self.setAlternatingRowColors(True)
        self.verticalHeader().setDefaultSectionSize(40)
        self.verticalHeader().setVisible(False)
        
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        
        # Styling
        self.setStyleSheet("""
            QTableView {
                background-color: white;
                alternate-background-color: #F8F9FA;
                gridline-color: #E0E0E0;
                border: none;
            }
            QTableView::item {
                padding: 4px;
                color: #000000;
            }
            QTableView::item:selected {
                background-color: #E8F5E8;
                color: #000000;
            }
        """)
        
        self.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #084924;
                color: white;
                padding: 8px 4px;
                border: none;
                border-right: 1px solid #0A5A2A;
                font-weight: bold;
                font-size: 11px;
                min-height: 70px;
            }
        """)
        
        self.horizontalHeader().setMinimumHeight(70)
        self.setWordWrap(True)
    
    def _update_header_colors(self):
        """Update header colors based on expand state"""
        expanded_main = None
        if self.data_model.get_column_state('midterm_expanded'):
            expanded_main = 'midterm'
        elif self.data_model.get_column_state('finalterm_expanded'):
            expanded_main = 'finalterm'
        
        all_states = dict(self.data_model.column_states)
        self.custom_header.set_expanded_states(expanded_main, all_states)
        self._create_all_option_widgets()
    
    def _create_all_option_widgets(self):
        """Create option widgets for all grade input cells"""
        for widget in self.cell_option_widgets.values():
            widget.deleteLater()
        self.cell_option_widgets = {}
        
        for row in range(self.table_model.rowCount()):
            for col in range(self.table_model.columnCount()):
                col_info = self.table_model.columns[col]
                if col_info.get('type') == 'grade_input':
                    self._create_option_widget(row, col)
    
    def _create_option_widget(self, row, col):
        """Create option widget for a specific cell"""
        widget = CellOptionsWidget(self.viewport())
        widget.upload_requested.connect(
            lambda r=row, c=col: self._on_upload_single(r, c)
        )
        widget.keep_draft_requested.connect(
            lambda r=row, c=col: self._on_keep_draft_single(r, c)
        )
        
        self._position_option_widget(row, col, widget)
        widget.show()
        
        self.cell_option_widgets[(row, col)] = widget
    
    def _position_option_widget(self, row, col, widget):
        """Position option widget in cell"""
        rect = self.visualRect(self.table_model.index(row, col))
        widget.setGeometry(
            rect.right() - 20,
            rect.top() + 2,
            18,
            rect.height() - 4
        )
    
    def _on_data_changed(self, top_left, bottom_right):
        """Handle data changes and update widgets"""
        for row in range(top_left.row(), bottom_right.row() + 1):
            for col in range(top_left.column(), bottom_right.column() + 1):
                if (row, col) in self.cell_option_widgets:
                    widget = self.cell_option_widgets[(row, col)]
                    self._position_option_widget(row, col, widget)
    
    def load_data(self, columns_info):
        """Load column structure and add bulk widgets"""
        self.table_model.setup_columns(columns_info)
        
        # Remove old bulk widgets
        for widget in self.custom_header.bulk_widgets.values():
            widget.deleteLater()
        self.custom_header.bulk_widgets = {}
        
        self._update_header_colors()
        
        # Set column widths and add bulk widgets
        for i, col_info in enumerate(columns_info):
            col_type = col_info.get('type', '')
            width = col_info.get('width', 100)
            
            self.setColumnWidth(i, width)
            
            if col_type == 'fixed':
                if i == 0:
                    self.setColumnWidth(i, 60)
                elif i == 1:
                    self.setColumnWidth(i, 220)
            
            elif col_type == 'grade_input':
                max_score = col_info.get('max_score', 40)
                widget = self.custom_header.create_bulk_widget(i, max_score)
                widget.show()
                self.custom_header.bulk_widgets[i] = widget
            
            elif col_type in ['expandable_main', 'expandable_component']:
                min_width = 140
                if width < min_width:
                    self.setColumnWidth(i, min_width)
            
            elif col_type == 'calculated':
                self.setColumnWidth(i, 110)
        
        # Position all bulk widgets
        self.custom_header.reposition_all_bulk_widgets()
        
        # Create option widgets for all grade cells
        self._create_all_option_widgets()
    
    def _on_header_expand(self, section, col_info):
        """Handle header expand/collapse"""
        self.controller.handle_header_expand_clicked(col_info)
    
    def _on_bulk_input(self, column, value):
        """Handle bulk input for a column"""
        self.table_model.bulk_set_grades(column, value)
    
    def _on_upload_column(self, column):
        """Handle upload column grades"""
        print(f"[DEBUG] Upload All clicked for column {column}")
        self.table_model.upload_column_grades(column)
    
    def _on_draft_column(self, column):
        """Handle keep as draft for column"""
        print(f"[DEBUG] Keep as Draft clicked for column {column}")
        col_info = self.table_model.columns[column]
        if col_info.get('type') == 'grade_input':
            component_key = col_info.get('component_key', '')
            for student_id in self.data_model.grades.keys():
                if component_key in self.data_model.grades[student_id]:
                    grade_item = self.data_model.grades[student_id][component_key]
                    if grade_item.value:
                        self.data_model.set_grade(student_id, component_key, grade_item.value, is_draft=True)
    
    def _on_upload_single(self, row, col):
        """Handle upload single grade"""
        print(f"[DEBUG] Upload clicked for cell ({row}, {col})")
        success = self.table_model.upload_single_grade(row, col)
        if success:
            print(f"[DEBUG] Grade uploaded successfully")

    def _on_keep_draft_single(self, row, col):
        """Handle keep as draft for single grade"""
        print(f"[DEBUG] Keep as Draft clicked for cell ({row}, {col})")
        col_info = self.table_model.columns[col]
        if col_info.get('type') == 'grade_input':
            component_key = col_info.get('component_key', '')
            student_id = self.data_model.students[row]['id']
            grade_item = self.data_model.get_grade(student_id, component_key)
            if grade_item.value:
                self.data_model.set_grade(student_id, component_key, grade_item.value, is_draft=True)
                print(f"[DEBUG] Grade kept as draft")
        
    def resizeEvent(self, event):
        """Reposition widgets on resize"""
        super().resizeEvent(event)
        self.custom_header.reposition_all_bulk_widgets()
        
        for (row, col), widget in self.cell_option_widgets.items():
            self._position_option_widget(row, col, widget)
    
    def scrollContentsBy(self, dx, dy):
        """Reposition widgets on scroll - bulk widgets auto-handled by viewport parent"""
        super().scrollContentsBy(dx, dy)
        
        # CRITICAL: Reposition bulk widgets on ANY scroll
        self.custom_header.reposition_all_bulk_widgets()
        
        # Reposition option widgets
        for (row, col), widget in self.cell_option_widgets.items():
            self._position_option_widget(row, col, widget)