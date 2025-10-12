from PyQt6.QtWidgets import QPushButton, QTableWidget, QHeaderView
from PyQt6.QtCore import Qt


def fit_button_text(button: QPushButton, padding: int = 12) -> None:
    """Adjust button minimum width so its text fits without clipping.

    - padding: extra horizontal pixels to add (left+right combined).
    """
    try:
        fm = button.fontMetrics()
        text = button.text() or ""
        # consider icon width if present
        icon_w = button.iconSize().width() if hasattr(button, "iconSize") else 0
        w = fm.horizontalAdvance(text) + padding + icon_w
        button.setMinimumWidth(w)
    except Exception:
        pass


def fit_all_buttons(container, padding: int = 12) -> None:
    """Recursively find QPushButton children and fit their widths."""
    try:
        buttons = container.findChildren(QPushButton)
        for b in buttons:
            fit_button_text(b, padding=padding)
    except Exception:
        pass


def auto_resize_table_columns(table: QTableWidget, policy: QHeaderView.ResizeMode = QHeaderView.ResizeMode.ResizeToContents) -> None:
    """Apply a sensible resize policy to table columns and rows to avoid clipping.

    - policy: default to ResizeToContents to size by content.
    """
    try:
        header = table.horizontalHeader()
        # If table is small and many columns, prefer Stretch to avoid horizontal scroll
        if table.columnCount() <= 4:
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        else:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # For vertical sizing, let rows fit contents
        table.resizeRowsToContents()
    except Exception:
        pass


def auto_resize_all_tables(container) -> None:
    """Find QTableWidget children and apply auto-resize logic."""
    try:
        tables = container.findChildren(QTableWidget)
        for t in tables:
            auto_resize_table_columns(t)
    except Exception:
        pass
