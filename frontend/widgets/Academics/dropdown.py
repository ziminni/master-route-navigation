from PyQt6.QtWidgets import QComboBox, QSizePolicy

class DropdownMenu(QComboBox):
    """
    A reusable dropdown menu widget based on QComboBox.
    Applies default styling but can be customized with a stylesheet.
    Supports adding items, setting default selections, and method chaining.

    Attributes:
        None (inherits all attributes from QComboBox).

    Args:
        items (list | None): A list of items to populate the dropdown.
        default_item (str | None): The item to display as default (must be in items).
        minimum_width (int | None): The minimum width of the dropdown.
        custom_style (bool): Whether to apply a custom stylesheet.
        stylesheet (str | None): The custom stylesheet string (if custom_style is True).
        parent (QWidget | None): The parent widget.
    """

    def __init__(self, items: list | None = None,
                  default_item: str | None = None,
                  minimum_width: int | None = None,
                  custom_style: bool = False,
                  stylesheet: str | None = None, 
                  parent: object | None = None):
        super().__init__(parent) 

        self.setMinimumHeight(45)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        if items:
            self.addItems(items)

        if default_item and default_item in items:
            self.setCurrentText(default_item)

        if minimum_width:
            self.setMinimumWidth(minimum_width)

        if custom_style and stylesheet:
            self.setStyleSheet(stylesheet)
        
        self.set_default_style() 

    def add_items(self, items: list):
        """
        Add multiple items to the dropdown.

        Args:
            items (list): List of items to add.

        Returns:
            DropdownMenu: The current instance for chaining.
        """
        self.addItems(items)
        return self 
    
    def add_item(self, item: str):
        """
        Add a single item to the dropdown.

        Args:
            item (str): The item to add.

        Returns:
            DropdownMenu: The current instance for chaining.
        """
        self.addItem(item)
        return self 
    
    def set_default_item(self, default_item: str):
        """
        Set the default selected item by text.

        Args:
            default_item (str): The text of the item to set as default.

        Returns:
            DropdownMenu: The current instance for chaining.
        """
        self.setCurrentText(default_item)
        return self 
    
    def set_minimum_width(self, minimum_width: int):
        """
        Set the minimum width of the dropdown.

        Args:
            minimum_width (int): The minimum width in pixels.

        Returns:
            DropdownMenu: The current instance for chaining.
        """
        self.setMinimumWidth(minimum_width)
        return self 
    
    def set_default_style(self):
        """
        Apply the default stylesheet for the dropdown.

        Returns:
            DropdownMenu: The current instance for chaining.
        """
        stylesheet = """
            QComboBox {
                padding: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
        """
        self.setStyleSheet(stylesheet)
        return self
    
    def set_custom_stylesheet(self, stylesheet: str):
        """
        Apply a custom stylesheet to the dropdown.

        Args:
            stylesheet (str): The custom stylesheet string.

        Returns:
            DropdownMenu: The current instance for chaining.
        """
        self.setStyleSheet(stylesheet)
        return self