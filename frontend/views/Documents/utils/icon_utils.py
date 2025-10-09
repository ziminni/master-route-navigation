"""
Icon Utility Module for Document Management System

This module provides utilities for loading and managing icons/images
for the document management interface.
"""

import os
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QPushButton, QLabel


class IconLoader:
    """
    Utility class for loading and managing icons from the Assets folder.
    
    This class provides methods to:
    - Load icons from the Assets folder
    - Create icon buttons
    - Create icon labels
    - Handle fallbacks if icons don't load
    """
    
    # Cache for loaded pixmaps to avoid reloading
    _icon_cache = {}
    
    @staticmethod
    def get_assets_path():
        """
        Get the absolute path to the assets folder.
        
        Returns:
            str: Absolute path to the assets folder
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_path = os.path.join(current_dir, '..', 'assets')
        return os.path.abspath(assets_path)
    
    @staticmethod
    def load_icon(icon_name, size=None, cache=True):
        """
        Load an icon from the Assets folder.
        
        Args:
            icon_name (str): Name of the icon file (e.g., 'menu-burger.png')
            size (tuple): Optional (width, height) tuple to scale the icon
            cache (bool): Whether to cache the loaded icon (default: True)
                        
        Returns:
            QPixmap: The loaded and optionally scaled pixmap, or None if failed
        """
        cache_key = f"{icon_name}_{size}" if size else icon_name
        
        # Check cache first
        if cache and cache_key in IconLoader._icon_cache:
            return IconLoader._icon_cache[cache_key]
        
        icon_path = os.path.join(IconLoader.get_assets_path(), icon_name)
        pixmap = QPixmap(icon_path)
        
        if pixmap.isNull():
            print(f"Warning: Failed to load icon '{icon_name}' from {icon_path}")
            return None
        
        # Scale if size provided
        if size:
            width, height = size
            pixmap = pixmap.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        
        # Cache the pixmap
        if cache:
            IconLoader._icon_cache[cache_key] = pixmap
        
        return pixmap
    
    @staticmethod
    def create_icon_button(icon_name, size=(24, 24), button_size=None, 
                          flat=True, tooltip=None, callback=None):
        """
        Create a QPushButton with an icon from the Assets folder.
        
        Args:
            icon_name (str): Name of the icon file (e.g., 'menu-burger.png')
            size (tuple): Size to scale the icon to (width, height)
            button_size (tuple): Optional fixed button size (width, height)
            flat (bool): Whether to make the button flat (no border)
            tooltip (str): Optional tooltip text
            callback (callable): Optional click callback function
            
        Returns:
            QPushButton: Configured button with icon
        """
        button = QPushButton()
        
        # Load and set icon
        pixmap = IconLoader.load_icon(icon_name, size)
        if pixmap:
            button.setIcon(QIcon(pixmap))
            button.setIconSize(QSize(size[0], size[1]))
        else:
            # Fallback: set text based on icon name
            fallback_text = IconLoader._get_fallback_text(icon_name)
            button.setText(fallback_text)
        
        # Configure button appearance
        if flat:
            button.setFlat(True)
        
        if button_size:
            button.setFixedSize(button_size[0], button_size[1])
        
        if tooltip:
            button.setToolTip(tooltip)
        
        if callback:
            button.clicked.connect(callback)
        
        return button
    
    @staticmethod
    def create_icon_label(icon_name, size=(24, 24), alignment=None):
        """
        Create a QLabel displaying an icon from the Assets folder.
        
        Args:
            icon_name (str): Name of the icon file (e.g., 'menu-burger.png')
            size (tuple): Size to scale the icon to (width, height)
            alignment (Qt.AlignmentFlag): Optional alignment for the label
            
        Returns:
            QLabel: Label displaying the icon
        """
        label = QLabel()
        
        # Load and set icon
        pixmap = IconLoader.load_icon(icon_name, size)
        if pixmap:
            label.setPixmap(pixmap)
        else:
            # Fallback: set text based on icon name
            fallback_text = IconLoader._get_fallback_text(icon_name)
            label.setText(fallback_text)
        
        if alignment:
            label.setAlignment(alignment)
        
        return label
    
    @staticmethod
    def get_qicon(icon_name, size=None):
        """
        Get a QIcon from the Assets folder.
        
        Args:
            icon_name (str): Name of the icon file (e.g., 'menu-burger.png')
            size (tuple): Optional size to scale the icon to (width, height)
            
        Returns:
            QIcon: The icon object, or empty QIcon if failed
        """
        pixmap = IconLoader.load_icon(icon_name, size)
        if pixmap:
            return QIcon(pixmap)
        return QIcon()
    
    @staticmethod
    def _get_fallback_text(icon_name):
        """
        Get fallback text for an icon based on its filename.
        
        Args:
            icon_name (str): Name of the icon file
            
        Returns:
            str: Fallback text
        """
        fallback_map = {
            'menu-burger.png': '☰',
            'search.png': '🔍',
            'add.png': '+',
            'delete.png': '🗑',
            'edit.png': '✏',
            'save.png': '💾',
            'download.png': '⬇',
            'upload.png': '⬆',
            'folder.png': '📁',
            'file.png': '📄',
        }
        return fallback_map.get(icon_name, '?')
    
    @staticmethod
    def clear_cache():
        """Clear the icon cache to free up memory."""
        IconLoader._icon_cache.clear()


# Convenience functions for common icons
def create_menu_button(callback=None):
    """
    Create a menu (hamburger) button.
    
    Args:
        callback (callable): Optional click callback
        
    Returns:
        QPushButton: Configured menu button
    """
    return IconLoader.create_icon_button(
        'menu-burger.png',
        size=(24, 24),
        button_size=(32, 32),
        flat=True,
        tooltip="Menu",
        callback=callback
    )


def create_search_button(callback=None):
    """
    Create a search button with search icon and "Search" text.
    
    Args:
        callback (callable): Optional click callback
        
    Returns:
        QPushButton: Configured search button with icon and text
    """
    button = QPushButton(" Search")
    
    # Load and set icon
    pixmap = IconLoader.load_icon('search.png', size=(20, 20))
    if pixmap:
        button.setIcon(QIcon(pixmap))
        button.setIconSize(QSize(20, 20))
    else:
        # Fallback: use search character
        button.setText("🔍 Search")
    
    button.setToolTip("Search")
    
    if callback:
        button.clicked.connect(callback)
    
    return button


def create_back_button(callback=None):
    """
    Create a back button with left arrow icon and "Back" text.
    
    Args:
        callback (callable): Optional click callback
        
    Returns:
        QPushButton: Configured back button with icon and text
    """
    button = QPushButton(" Back")
    
    # Load and set icon
    pixmap = IconLoader.load_icon('left.png', size=(20, 20))
    if pixmap:
        button.setIcon(QIcon(pixmap))
        button.setIconSize(QSize(20, 20))
    else:
        # Fallback: use arrow character
        button.setText("← Back")
    
    button.setToolTip("Go back to previous view")
    
    if callback:
        button.clicked.connect(callback)
    
    return button


def create_floating_add_button(callback=None):
    """
    Create a floating action button (FAB) with add icon for bottom-right corner.
    
    This creates a circular button with the add.png icon that can be positioned
    in the bottom-right corner of a view for quick access to add file functionality.
    
    Args:
        callback (callable): Optional click callback
        
    Returns:
        QPushButton: Configured floating action button
    """
    button = QPushButton()
    
    # Load and set icon
    pixmap = IconLoader.load_icon('add.png', size=(32, 32))
    if pixmap:
        button.setIcon(QIcon(pixmap))
        button.setIconSize(QSize(32, 32))
    else:
        # Fallback: use plus character
        button.setText("+")
        button.setStyleSheet("font-size: 24px; font-weight: bold;")
    
    # Style as circular floating action button
    button.setFixedSize(56, 56)
    button.setToolTip("Add File")
    
    if callback:
        button.clicked.connect(callback)
    
    return button
