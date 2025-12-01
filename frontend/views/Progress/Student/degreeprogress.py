# frontend/views/Progress/Student/degreeprogress.py
import threading
import traceback
import requests

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np


class DegreeProgressWidget(QWidget):
    """
    Thread-safe: background fetch emits 'degree_loaded' and UI updates run in main thread.
    """
    degree_loaded = pyqtSignal(dict)  # emits backend payload dict

    def __init__(self, token=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.token = token or ""
        self.api_base = api_base.rstrip("/")

        # data containers
        self.all_semesters_data = {}
        self.category_totals = {}
        self.category_progress = {}  # Use backend-provided progress percentages
        self.current_semester = None

        self.init_ui()

        # connect signal then start worker
        self.degree_loaded.connect(self._on_degree_progress_loaded_slot)
        self.load_degree_progress_from_backend_async()

    # ---------------------------------------------------------
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Header with progress summary
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        self.summary_label = QLabel("Overall Progress: --")
        summary_font = QFont()
        summary_font.setPointSize(12)
        summary_font.setBold(True)
        self.summary_label.setFont(summary_font)
        
        header_layout.addWidget(self.summary_label)
        header_layout.addStretch()
        main_layout.addWidget(header_widget)

        self.table = self.create_table()
        main_layout.addWidget(self.table)

        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(5)

        # left donut - overall progress
        self.circular_canvas = FigureCanvas(plt.Figure(figsize=(3, 3)))
        self.circular_ax = self.circular_canvas.figure.add_subplot(111)
        charts_layout.addWidget(self.circular_canvas, stretch=1)

        # right bars - category progress
        self.bar_canvas = FigureCanvas(plt.Figure(figsize=(4, 2)))
        self.bar_ax = self.bar_canvas.figure.add_subplot(111)
        charts_layout.addWidget(self.bar_canvas, stretch=2)

        main_layout.addLayout(charts_layout)
        self.setObjectName("degreeProgressWidget")

    # ---------------------------------------------------------
    def create_table(self):
        table = QTableWidget()
        table.setObjectName("degreeProgressTable")

        headers = ["No", "Subject Code", "Description", "Units", "Year & Term", "Midterm", "Finals", "Status"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        # Set alternating row colors
        table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)

        widths = [40, 100, 200, 60, 120, 70, 70, 80]
        header = table.horizontalHeader()
        for i, w in enumerate(widths):
            if w == 200:  # Description column is stretchable
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                table.setColumnWidth(i, w)

        return table

    # ---------------------------------------------------------
    def _build_headers(self):
        token = (self.token or "").strip()
        if not token:
            return {}
        if token.startswith("Bearer ") or token.startswith("Token "):
            return {"Authorization": token}
        if len(token) > 40:
            return {"Authorization": f"Bearer {token}"}
        return {"Authorization": f"Token {token}"}

    # ---------------------------------------------------------
    def load_degree_progress_from_backend_async(self):
        """GET /api/progress/student/degreeprogress/"""
        url = f"{self.api_base}/api/progress/student/degreeprogress/"
        headers = self._build_headers()

        def fetch():
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    self.degree_loaded.emit(data)
                else:
                    self.degree_loaded.emit({})
            except Exception:
                traceback.print_exc()
                self.degree_loaded.emit({})

        threading.Thread(target=fetch, daemon=True).start()
        
    # ---------------------------------------------------------
    @pyqtSlot(dict)
    def _on_degree_progress_loaded_slot(self, data):
        """
        Runs on main thread. Safe to update widgets here.
        """
        if isinstance(data, dict):
            self.all_semesters_data = data.get("semesters", {}) or {}
            self.category_totals = data.get("category_totals", {}) or {}
            self.category_progress = data.get("category_progress", {}) or {}
        else:
            self.all_semesters_data = {}
            self.category_totals = {}
            self.category_progress = {}

        if self.all_semesters_data:
            # Get the most recent semester
            semesters = list(self.all_semesters_data.keys())
            # Try to sort chronologically (most recent first)
            try:
                # Simple sorting - assumes format like "2024-2025 – first"
                semesters.sort(key=lambda x: x.split(' – ')[0] if ' – ' in x else x, reverse=True)
            except:
                pass
            
            if semesters:
                self.current_semester = semesters[0]
                self.load_semester_data(self.current_semester)
        
        # Update charts with backend-provided progress data
        self._update_charts()

    # ---------------------------------------------------------
    def load_semester_data(self, semester):
        sem_data = self.all_semesters_data.get(semester, {})
        subjects = sem_data.get("subjects", [])
        self.table.setRowCount(0)

        for subj_idx, subj in enumerate(subjects, start=1):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Get grades - handle both dict and string formats
            grades = subj.get("grades", {})
            if isinstance(grades, dict):
                midterm = grades.get("midterm", "")
                finals = grades.get("finals", "")
                
                # Determine status based on final grade
                status = ""
                try:
                    final_grade = float(finals) if finals else None
                    if final_grade is not None:
                        if final_grade <= 3.0:
                            status = "PASSED"
                        elif final_grade <= 4.0:
                            status = "CONDITIONAL"
                        else:
                            status = "FAILED"
                except:
                    status = ""
            else:
                midterm = ""
                finals = str(grades) if grades else ""
                status = ""

            items = [
                str(subj_idx),
                subj.get("subject_code", ""),
                subj.get("description", ""),
                str(subj.get("units", "")),
                subj.get("year_term", semester),  # Use semester if year_term not provided
                str(midterm),
                str(finals),
                status
            ]

            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(QFont("Poppins", 9))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Color code the status column
                if col == 7:  # Status column
                    if val == "PASSED":
                        item.setBackground(QColor(220, 255, 220))  # Light green
                    elif val == "FAILED":
                        item.setBackground(QColor(255, 220, 220))  # Light red
                    elif val == "CONDITIONAL":
                        item.setBackground(QColor(255, 255, 200))  # Light yellow
                
                self.table.setItem(row, col, item)

        self.table.resizeRowsToContents()

    # ---------------------------------------------------------
    def set_semester(self, semester):
        """
        Called by parent GradesWidget when semester changes.
        """
        if not semester:
            return
        self.current_semester = semester
        self.load_semester_data(semester)
        
        # Also update summary label
        if self.category_progress:
            overall = sum(self.category_progress.values()) / len(self.category_progress) if self.category_progress else 0
            self.summary_label.setText(f"Overall Progress: {overall:.1f}%")

    # ---------------------------------------------------------
    def _update_charts(self):
        """Update both charts with backend-provided progress data"""
        self._plot_circular()
        self._plot_bars()
        
        # Update summary label
        if self.category_progress:
            overall = sum(self.category_progress.values()) / len(self.category_progress) if self.category_progress else 0
            self.summary_label.setText(f"Overall Progress: {overall:.1f}%")
        else:
            self.summary_label.setText("Overall Progress: --")

    def _plot_circular(self):
        """Plot donut chart for overall progress"""
        self.circular_ax.clear()
        
        # Calculate overall progress from category progress
        overall = 0
        if self.category_progress:
            overall = sum(self.category_progress.values()) / len(self.category_progress)
        
        sizes = [overall, max(0, 100 - overall)]
        colors = ['#4CAF50', '#E0E0E0']  # Green for progress, gray for remaining
        
        # FIXED: In newer matplotlib, pie() returns only wedges, texts
        wedges, texts = self.circular_ax.pie(
            sizes,
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.3, edgecolor='white', linewidth=2)
        )
        
        # Center text
        self.circular_ax.text(0, 0, f"{overall:.0f}%", 
                             ha='center', va='center',
                             fontsize=20, fontweight='bold',
                             color='#333333')
        
        self.circular_ax.set_aspect('equal')
        self.circular_ax.set_title("Overall Progress", fontsize=10, fontweight='bold', pad=10)
        self.circular_canvas.draw()

    # ---------------------------------------------------------
    def _plot_bars(self):
        """Plot horizontal bar chart for category progress"""
        self.bar_ax.clear()
        
        if not self.category_progress:
            self.bar_ax.text(0.5, 0.5, 'No progress data',
                            ha='center', va='center', transform=self.bar_ax.transAxes,
                            fontsize=12, color='gray')
            self.bar_canvas.draw()
            return
        
        # Prepare data for bar chart
        categories = list(self.category_progress.keys())
        progress_values = list(self.category_progress.values())
        
        # Get total required for each category
        totals = [self.category_totals.get(cat, 0) for cat in categories]
        
        # Create horizontal bars
        y_pos = np.arange(len(categories))
        
        # Plot bars
        bars = self.bar_ax.barh(y_pos, progress_values, height=0.6, color='#3498db')
        
        # Add value labels on bars
        for i, (pct, total) in enumerate(zip(progress_values, totals)):
            # Calculate completed count
            completed = int(total * pct / 100) if pct > 0 else 0
            
            # Add percentage label inside bar
            if pct > 20:  # Only put label inside if bar is wide enough
                self.bar_ax.text(pct / 2, i, f"{pct:.0f}%", 
                               ha='center', va='center', 
                               fontsize=9, fontweight='bold', color='white')
            
            # Add count label at the end
            self.bar_ax.text(pct + 1, i, f"{completed}/{total}", 
                           ha='left', va='center', 
                           fontsize=8, color='#333333')
        
        # Set y-axis labels
        self.bar_ax.set_yticks(y_pos)
        self.bar_ax.set_yticklabels(categories, fontsize=9)
        
        # Set x-axis limits and labels
        self.bar_ax.set_xlim(0, 100)
        self.bar_ax.set_xlabel("Progress (%)", fontsize=9)
        
        # Add grid
        self.bar_ax.grid(True, axis='x', linestyle='--', alpha=0.3)
        
        self.bar_ax.set_title("Category Progress", fontsize=10, fontweight='bold', pad=10)
        self.bar_canvas.figure.tight_layout()
        self.bar_canvas.draw()

    # ---------------------------------------------------------
    def refresh_data(self):
        """Public method to refresh degree progress data"""
        self.load_degree_progress_from_backend_async()