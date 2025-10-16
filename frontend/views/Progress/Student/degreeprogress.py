import os
import json
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Circle, Wedge
import seaborn as sns
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
from PyQt6.QtGui import QFont
import pandas as pd


class DegreeProgressWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.progress_data = {}
        self.subjects_data = []
        self.all_semesters_data = {}
        self.current_semester = None
        self.category_totals = {}
        self.file_watcher = QFileSystemWatcher(self)

        # File path for JSON
        self.subjects_file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "student_degreeProgress.json"
        )

        self.init_ui()
        self.load_subjects_from_file()

        # Watch file for live reload
        if os.path.exists(self.subjects_file_path):
            self.file_watcher.addPath(self.subjects_file_path)
        self.file_watcher.fileChanged.connect(self.on_file_changed)

    # ---------------------------------------------------------
    def init_ui(self):
        """Initialize the UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # --- Table ---
        self.table = self.create_table()
        main_layout.addWidget(self.table)

        # --- Charts ---
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(5)

        # Circular chart (left)
        self.circular_canvas = FigureCanvas(plt.Figure(figsize=(3, 3)))
        self.circular_ax = self.circular_canvas.figure.add_subplot(111)
        charts_layout.addWidget(self.circular_canvas, stretch=1)

        # Bar charts (right)
        self.bar_canvas = FigureCanvas(plt.Figure(figsize=(4, 2)))
        self.bar_ax = self.bar_canvas.figure.add_subplot(111)
        charts_layout.addWidget(self.bar_canvas, stretch=2)

        main_layout.addLayout(charts_layout)
        self.setObjectName("degreeProgressWidget")

    # ---------------------------------------------------------
    def create_table(self):
        """Create and configure the subjects table"""
        table = QTableWidget()
        table.setObjectName("degreeProgressTable")

        headers = ["No", "Subject Code", "Description", "Units", "Year & Term", "Grades", "Pre-Requisites"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(False)

        # Column widths
        widths = [50, 120, 0, 80, 180, 80, 120]
        header = table.horizontalHeader()
        for i, w in enumerate(widths):
            if w == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                table.setColumnWidth(i, w)

        return table

    # ---------------------------------------------------------
    def load_subjects_from_file(self):
        """Load the degree progress data from JSON"""
        if not os.path.exists(self.subjects_file_path):
            print(f"⚠️ File not found: {self.subjects_file_path}")
            return

        try:
            with open(self.subjects_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.all_semesters_data = data.get("semesters", {})
            self.category_totals = data.get("category_totals", {})

            if self.all_semesters_data:
                # Default to the latest semester
                self.current_semester = list(self.all_semesters_data.keys())[-1]
                self.load_semester_data(self.current_semester)

        except Exception as e:
            print(f"❌ Error reading student_degreeProgress.json: {e}")

    # ---------------------------------------------------------
    def load_semester_data(self, semester):
        """Display semester subjects and update progress"""
        semester_data = self.all_semesters_data.get(semester, {})
        subjects = semester_data.get("subjects", [])
        self.table.setRowCount(0)

        for subj in subjects:
            row = self.table.rowCount()
            self.table.insertRow(row)

            items = [
                str(subj.get("no", "")),
                subj.get("subject_code", ""),
                subj.get("description", ""),
                str(subj.get("units", "")),
                subj.get("year_term", ""),
                str(subj.get("grades", "")),
                subj.get("pre_requisites", "")
            ]

            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(QFont("Poppins", 9))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)

        self.table.resizeRowsToContents()

        # Update charts using all subjects
        all_subjects = []
        for sem_data in self.all_semesters_data.values():
            all_subjects.extend(sem_data.get("subjects", []))

        self.calculate_progress_from_subjects(all_subjects)

        print(f"📘 Degree Progress loaded for {semester}")

    # ---------------------------------------------------------
    def set_semester(self, semester):
        """Sync semester from GradesWidget"""
        if not semester or semester not in self.all_semesters_data:
            return
        self.current_semester = semester
        self.load_semester_data(semester)

    # ---------------------------------------------------------
    def on_file_changed(self, path):
        """Reload JSON if it changes"""
        print(f"🔄 Detected change in {path}, reloading...")
        if path == self.subjects_file_path:
            self.load_subjects_from_file()
        if os.path.exists(self.subjects_file_path):
            if self.subjects_file_path not in self.file_watcher.files():
                self.file_watcher.addPath(self.subjects_file_path)

    # ---------------------------------------------------------
    def calculate_progress_from_subjects(self, subjects):
        """Compute progress per category and overall"""
        category_counts = {}
        for subj in subjects:
            category = subj.get("category", "")
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1

        total_completed = sum(category_counts.values())
        total_required = sum(self.category_totals.values())
        overall_progress = int((total_completed / total_required * 100)) if total_required > 0 else 0

        categories = []
        for name, total in self.category_totals.items():
            completed = category_counts.get(name, 0)
            percent = int((completed / total * 100)) if total > 0 else 0
            categories.append({
                "name": name,
                "completed": completed,
                "total": total,
                "percentage": percent
            })

        self.progress_data = {
            "overall_progress": overall_progress,
            "categories": categories
        }
        self.update_charts()

    # ---------------------------------------------------------
    def update_charts(self):
        self.plot_circular_progress()
        self.plot_horizontal_bars()

    def plot_circular_progress(self):
        """Draw donut chart"""
        self.circular_ax.clear()
        overall = self.progress_data.get("overall_progress", 0)

        sizes = [overall, 100 - overall]
        colors = ['#2c5530', '#E8E8E8']

        self.circular_ax.pie(
            sizes,
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.3, edgecolor='white', linewidth=2)
        )
        self.circular_ax.text(0, 0, f"{overall}%", ha='center', va='center',
                              fontsize=20, fontweight='bold', color='#2c5530')
        self.circular_ax.text(0, -0.25, 'Degree Progress', ha='center',
                              va='center', fontsize=7, color='#666666')

        self.circular_ax.set_aspect('equal')
        self.circular_canvas.draw()

    def plot_horizontal_bars(self):
        """Draw horizontal category bars"""
        self.bar_ax.clear()
        categories = self.progress_data.get("categories", [])
        if not categories:
            return

        names = [c["name"] for c in categories][::-1]
        percents = [c["percentage"] for c in categories][::-1]
        labels = [f"{c['completed']} of {c['total']} Progress" for c in categories][::-1]

        sns.set_style("whitegrid")
        y_pos = range(len(names))

        self.bar_ax.barh(y_pos, percents, color='#2c5530', height=0.6)
        self.bar_ax.barh(y_pos, [100 - p for p in percents], left=percents,
                         color='#E8E8E8', height=0.6)

        for i, (pct, label) in enumerate(zip(percents, labels)):
            self.bar_ax.text(pct / 2, i, f"{int(pct)}%", ha='center', va='center',
                             fontsize=6, fontweight='bold', color='white')
            self.bar_ax.text(2, i - 0.35, label, ha='left', va='center',
                             fontsize=5, color='#666666')

        self.bar_ax.set_yticks(y_pos)
        self.bar_ax.set_yticklabels(names, fontsize=7, fontweight='bold')
        self.bar_ax.set_xlim(0, 100)
        self.bar_ax.set_xticks([])
        self.bar_ax.spines['top'].set_visible(False)
        self.bar_ax.spines['right'].set_visible(False)
        self.bar_ax.spines['bottom'].set_visible(False)
        self.bar_ax.spines['left'].set_visible(False)
        self.bar_ax.grid(False)
        self.bar_canvas.figure.tight_layout()
        self.bar_canvas.draw()