from PyQt6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, QVariant
)
from PyQt6.QtGui import QColor, QFont, QBrush

class GradesTableModel(QAbstractTableModel):
    """
    Table model for grades with draft/upload status support.
    UPDATED: Better color differentiation and percentage display
    """
    
    # Custom roles
    IsDraftRole = Qt.ItemDataRole.UserRole + 1
    ComponentKeyRole = Qt.ItemDataRole.UserRole + 2
    ColumnInfoRole = Qt.ItemDataRole.UserRole + 3
    
    def __init__(self, data_model, controller, parent=None):
        super().__init__(parent)
        self.data_model = data_model
        self.controller = controller
        self.columns = []  # List of column info dicts
        
    def setup_columns(self, columns_info):
        """Setup columns based on rubric configuration"""
        self.beginResetModel()
        self.columns = columns_info
        self.endResetModel()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.data_model.students)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        row, col = index.row(), index.column()
        if col >= len(self.columns):
            return QVariant()
            
        col_info = self.columns[col]
        col_type = col_info.get('type', '')
        student = self.data_model.students[row]
        
        # Student ID column
        if col == 0:
            if role == Qt.ItemDataRole.DisplayRole:
                return student['id']
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignCenter
        
        # Student Name column
        elif col == 1:
            if role == Qt.ItemDataRole.DisplayRole:
                return student['name']
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        # Grade input columns
        elif col_type == 'grade_input':
            component_key = col_info.get('component_key', '')
            grade_item = self.data_model.get_grade(student['id'], component_key)
            
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return grade_item.value
            elif role == self.IsDraftRole:
                return grade_item.is_draft
            elif role == self.ComponentKeyRole:
                return component_key
            elif role == Qt.ItemDataRole.BackgroundRole:
                # Three distinct colors for empty, draft, and uploaded
                if not grade_item.value:
                    return QBrush(QColor("#FFFFFF"))  # White for empty
                elif grade_item.is_draft:
                    return QBrush(QColor("#FFF4E6"))  # Light orange for draft
                else:
                    return QBrush(QColor("#D1F2EB"))  # Light teal for uploaded
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignCenter
        
        # Expandable component columns (show aggregated scores)
        elif col_type == 'expandable_component':
            if role == Qt.ItemDataRole.DisplayRole:
                component = col_info.get('component')
                term = col_info.get('term')
                if component and term:
                    # Get component name from the component key
                    comp_name = component.replace('_', ' ')
                    avg = self.controller.calculate_component_average(
                        student['id'], comp_name, term
                    )
                    return avg if avg else ""
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignCenter
            elif role == Qt.ItemDataRole.BackgroundRole:
                return QBrush(QColor("#E8F5E9"))  # Light green background
            elif role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setBold(True)
                return font
        
        # Calculated columns (main term averages with /100, final grade)
        elif col_type in ['calculated', 'expandable_main']:
            if role == Qt.ItemDataRole.DisplayRole:
                return self._calculate_display_value(row, col_info)
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignCenter
            elif role == Qt.ItemDataRole.BackgroundRole:
                return QBrush(QColor("#E3F2FD"))  # Light blue background
            elif role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setBold(True)
                return font
        
        # Store column info for header
        if role == self.ColumnInfoRole:
            return col_info
        
        return QVariant()
    
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        
        row, col = index.row(), index.column()
        col_info = self.columns[col]
        
        if col_info.get('type') == 'grade_input':
            component_key = col_info.get('component_key', '')
            student_id = self.data_model.students[row]['id']
            
            if role == Qt.ItemDataRole.EditRole:
                self.data_model.set_grade(student_id, component_key, value, is_draft=True)
                self.dataChanged.emit(index, index)
                # Emit changes for calculated columns
                self._emit_calculated_changes(row)
                return True
        
        return False
    
    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        col_info = self.columns[index.column()]
        if col_info.get('type') == 'grade_input':
            return (Qt.ItemFlag.ItemIsEnabled | 
                    Qt.ItemFlag.ItemIsSelectable | 
                    Qt.ItemFlag.ItemIsEditable)
        
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                if section < len(self.columns):
                    return self.columns[section].get('name', '')
            elif role == self.ColumnInfoRole:
                if section < len(self.columns):
                    return self.columns[section]
        return QVariant()
    
    def _calculate_display_value(self, row, col_info):
        """Calculate display value for calculated columns with /100 for term grades"""
        col_name = col_info.get('name', '')
        student_id = self.data_model.students[row]['id']
        calculated = self.controller.calculate_grades_for_student(student_id)
        
        if 'Midterm Grade' in col_name:
            # Show as percentage out of 100
            return f"{calculated['midterm_avg']}/100"
        elif 'Final Term Grade' in col_name:
            # Show as percentage out of 100
            return f"{calculated['finalterm_avg']}/100"
        elif 'Final Grade' in col_name:
            # Final grade shows just the percentage
            return calculated['final_grade']
        
        return "0.00"
    
    def _emit_calculated_changes(self, row):
        """Emit dataChanged for all calculated columns in a row"""
        for col, col_info in enumerate(self.columns):
            if col_info.get('type') in ['calculated', 'expandable_main', 'expandable_component']:
                index = self.index(row, col)
                self.dataChanged.emit(index, index)
    
    def bulk_set_grades(self, col, value):
        """Set grade value for all students in a column"""
        col_info = self.columns[col]
        if col_info.get('type') != 'grade_input':
            return
        
        component_key = col_info.get('component_key', '')
        self.data_model.bulk_set_grades(component_key, value)
        
        # Emit changes for entire column
        top_left = self.index(0, col)
        bottom_right = self.index(self.rowCount() - 1, col)
        self.dataChanged.emit(top_left, bottom_right)
        
        # Update calculated columns
        for row in range(self.rowCount()):
            self._emit_calculated_changes(row)
    
    def upload_column_grades(self, col):
        """Mark all grades in column as uploaded"""
        col_info = self.columns[col]
        if col_info.get('type') != 'grade_input':
            return
        
        component_key = col_info.get('component_key', '')
        self.data_model.upload_grades(component_key)
        
        # Emit changes for entire column
        top_left = self.index(0, col)
        bottom_right = self.index(self.rowCount() - 1, col)
        self.dataChanged.emit(top_left, bottom_right)
    
    def upload_single_grade(self, row, col):
        """Mark a single grade as uploaded"""
        col_info = self.columns[col]
        if col_info.get('type') != 'grade_input':
            return False
        
        component_key = col_info.get('component_key', '')
        student_id = self.data_model.students[row]['id']
        
        grade_item = self.data_model.get_grade(student_id, component_key)
        if grade_item.value:
            self.data_model.set_grade(student_id, component_key, grade_item.value, is_draft=False)
            index = self.index(row, col)
            self.dataChanged.emit(index, index)
            return True
        return False