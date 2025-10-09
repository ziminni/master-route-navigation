from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRect


class DonutChartWidget(QWidget):
    """
    this is the custom widget to display storage usage as a donut chart
    """
    def __init__(self, used_percentage, used_gb, total_gb, parent=None):
        super().__init__(parent)
        self.used_percentage = used_percentage
        self.used_gb = used_gb
        self.total_gb = total_gb
        self.setMinimumSize(200, 200)
        
    def update_data(self, used_percentage, used_gb, total_gb):
        """Update chart data and redraw"""
        self.used_percentage = used_percentage
        self.used_gb = used_gb
        self.total_gb = total_gb
        self.update()  # this triggers the paintEvent method
    
    def paintEvent(self, event):
        """Custom paint event to draw the donut chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate chart area (leave some margin)
        margin = 20
        chart_rect = QRect(margin, margin, 
                          self.width() - 2 * margin, 
                          self.height() - 2 * margin)
        
        # Make it square (use the smaller dimension)
        size = min(chart_rect.width(), chart_rect.height())
        chart_rect.setWidth(size)
        chart_rect.setHeight(size)
        
        # Center the square
        chart_rect.moveCenter(self.rect().center())
        
        # Define donut thickness
        donut_thickness = 25
        
        # Define colors
        used_color = QColor("#084924")  # Green for used storage
        free_color = QColor("#E0E0E0")  # Light gray for free storage
        
        # Draw the background (free space) donut
        painter.setPen(QPen(free_color, donut_thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill, just the outline
        painter.drawEllipse(chart_rect)
        
        # Calculate the angle for used storage (360 degrees = 100%)
        used_angle = int((self.used_percentage / 100.0) * 360 * 16)  # Qt uses 1/16th degrees
        
        # Draw the used storage arc (donut style)
        painter.setPen(QPen(used_color, donut_thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill, just the outline
        painter.drawArc(chart_rect, 90 * 16, -used_angle)  # Start from top (90 degrees)
        
        # Calculate center area for text
        center_rect = QRect(chart_rect.x() + donut_thickness + 20, 
                           chart_rect.y() + donut_thickness + 20,
                           chart_rect.width() - 2 * (donut_thickness + 20), 
                           chart_rect.height() - 2 * (donut_thickness + 20))
        
        # Draw percentage in center
        painter.setPen(QColor("#084924"))  # Green color to match the donut
        painter.setFont(QFont("Poppins", 24, QFont.Weight.Bold))
        
        # Create rect for percentage (top half of center)
        percentage_rect = QRect(center_rect.x(), center_rect.y(),
                               center_rect.width(), center_rect.height() // 2)
        painter.drawText(percentage_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, 
                        f"{self.used_percentage}%")
        
        # Draw total size under percentage (bottom half of center)
        painter.setPen(QColor("#084924"))  # green color for subtitle
        painter.setFont(QFont("Poppins", 10))  
        size_rect = QRect(center_rect.x(), center_rect.y() + center_rect.height() // 2,
                         center_rect.width(), center_rect.height() // 2)
        painter.drawText(size_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop,
                        f"Total Size: {self.total_gb:.1f} GB")
