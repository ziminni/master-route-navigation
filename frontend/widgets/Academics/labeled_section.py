from PyQt6.QtWidgets import QLabel, QFrame, QWidget, QHBoxLayout, QVBoxLayout
from .dropdown import DropdownMenu 

class LabeledSection(QFrame):
    """
    A reusable composite widget that combines a label with another widget (e.g., input fields, dropdowns).
    Can be arranged either vertically or horizontally, and supports optional sublabels for additional context.

    Attributes:
        __is_vertical (bool): Whether the layout is vertical (True) or horizontal (False).
        __label (QLabel): The main label displayed in the section.
        __sublabels (list[QLabel]): A list of sublabels added below or above the main label.
        __layout (QVBoxLayout | QHBoxLayout): The layout managing label(s) and content widget.

    Args:
        label (str): The text for the main label.
        widget (QWidget): The main content widget (e.g., input field, dropdown).
        sub_label (str | None): Optional sublabel text.
        vertical_layout (bool): True for vertical layout, False for horizontal.
        label_first (bool): If True, the label is placed before the widget.
        sublabel_pos (int): Position of the sublabel relative to the main label and widget.
            - 0: directly above the main label
            - 1: directly below the main label
            - 2 or higher: directly below the widget
        parent (QWidget | None): The parent widget.
    """

    def __init__(self, label:str, 
                 widget: QWidget,
                 sub_label: str| None = None,
                 vertical_layout: bool = True, 
                 label_first: bool = True,
                 sublabel_pos: int = 1,
                 parent=None):
        super().__init__(parent)

        self.__is_vertical = vertical_layout
        self.__label = self.setup_label(label)
        self.__sublabels = [] 
        
        self.__layout = QVBoxLayout(self) if vertical_layout else QHBoxLayout(self)
        self.__layout.setSpacing(10)

        if label_first: 
            self.__layout.addWidget(self.__label)
            self.__layout.addWidget(widget)
        else: 
            self.__layout.addWidget(widget)
            self.__layout.addWidget(self.__label)

        if sub_label:
            self.add_sublabel(sub_label, sublabel_pos)

    def setup_label(self, label: str):
        """
        Create and return a styled QLabel for the main section label.

        Args:
            label (str): The text to display in the label.

        Returns:
            QLabel: A styled label widget.
        """
        label = QLabel(label)
        label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        return label 
    
    def setContentSpacing(self, spacing: int):
        """
        Set the spacing between child widgets in the layout.

        Args:
            spacing (int): The number of pixels to use as spacing.

        Returns:
            LabeledSection: The current instance for chaining.
        """
        self.__layout.setSpacing(spacing)
        return self 
    
    def add_sublabel(self, label:str, position: int = 1) -> QLabel | None: 
        """
        Add a sublabel (smaller label) for additional context or hints.
        Only applicable when using vertical layouts.

        Args:
            label (str): The text to display in the sublabel.
            position (int): The position for the sublabel.
                - 0: Directly above the main label
                - 1: Directly below the main label
                - 2 or higher: Directly below the widget

        Returns:
            QLabel | None: The created sublabel if added, None if layout is not vertical.
        """
        if not self.__is_vertical:
            return None 
        
        sublabel = QLabel(label)
        sublabel.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 12px;
                border: none;
            }
        """)

        if position == 0:
            self.__layout.insertWidget(0, sublabel)
        elif position == 1:
            self.__layout.insertWidget(1, sublabel)
        else: 
            self.__layout.addWidget(sublabel)
        
        self.__sublabels.append(sublabel)
        return sublabel
