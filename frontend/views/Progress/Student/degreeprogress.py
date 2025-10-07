import os
import json
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Circle, Wedge
import seaborn as sns
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
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
        self.current_semester = "2025-2026 1st Sem"  # Default semester
        self.file_watcher = QFileSystemWatcher(self)
        
        self.subjects_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "degree_progress_subjects.json")
        
        self.init_ui()
        self.load_subjects_from_file()  # This will calculate progress automatically
        
        # Start watching the subjects file
        if os.path.exists(self.subjects_file_path):
            self.file_watcher.addPath(self.subjects_file_path)
        self.file_watcher.fileChanged.connect(self.on_file_changed)
    
    def init_ui(self):
        """Initialize the UI layout"""
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Table at the top
        self.table = self.create_table()
        main_layout.addWidget(self.table)
        
        # Charts layout (horizontal)
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(5)  # Small margin to make them look connected
        
        # Left side: Circular progress chart
        self.circular_canvas = FigureCanvas(plt.Figure(figsize=(3, 3)))
        self.circular_ax = self.circular_canvas.figure.add_subplot(111)
        charts_layout.addWidget(self.circular_canvas, stretch=1)
        
        # Right side: Horizontal bar charts
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.bar_canvas = FigureCanvas(plt.Figure(figsize=(4, 1.5)))
        self.bar_ax = self.bar_canvas.figure.add_subplot(111)
        right_layout.addWidget(self.bar_canvas)
        
        charts_layout.addWidget(right_widget, stretch=2)
        
        main_layout.addLayout(charts_layout)
        
        self.setObjectName("degreeProgressWidget")
    
    def create_table(self):
        """Create the subjects table"""
        table = QTableWidget()
        table.setObjectName("degreeProgressTable")
        
        headers = ["No", "Subject Code", "Description", "Units", "Year & Term", "Grades", "Pre-Requisites"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        table.horizontalHeader().setStretchLastSection(False)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(False)
        
        # Make table read-only
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Column widths
        header = table.horizontalHeader()
        widths = [50, 120, 0, 80, 180, 80, 120]  # 0 means stretch
        for i, width in enumerate(widths):
            if width == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                table.setColumnWidth(i, width)
        
        # Table will dynamically size based on content - no scrolling
        table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        return table
    
    def load_subjects_from_file(self):
        """Load subjects data from JSON file and calculate progress"""
        if not os.path.exists(self.subjects_file_path):
            print(f"⚠️ File not found: {self.subjects_file_path}")
            return
        
        try:
            with open(self.subjects_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Store all semesters data
            self.all_semesters_data = data.get("semesters", {})
            self.category_totals = data.get("category_totals", {})
            
            # Load data for current semester
            self.load_semester_data(self.current_semester)
            
        except Exception as e:
            print(f"❌ Error reading degree_progress_subjects.json: {e}")
    
    def load_semester_data(self, semester):
        """Load and display data for a specific semester"""
        semester_data = self.all_semesters_data.get(semester, {})
        subjects = semester_data.get("subjects", [])
        
        # Clear existing table data
        self.table.setRowCount(0)
        
        # Add rows from JSON
        for subject in subjects:
            row_count = self.table.rowCount()
            self.table.insertRow(row_count)
            
            items = [
                str(subject.get("no", "")),
                subject.get("subject_code", ""),
                subject.get("description", ""),
                str(subject.get("units", "")),
                subject.get("year_term", ""),
                str(subject.get("grades", "")),
                subject.get("pre_requisites", "")
            ]
            
            for col, value in enumerate(items):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_count, col, item)
        
        self.table.resizeRowsToContents()
        
        # Calculate progress from ALL subjects across all semesters
        all_subjects = []
        for sem_data in self.all_semesters_data.values():
            all_subjects.extend(sem_data.get("subjects", []))
        
        self.calculate_progress_from_subjects(all_subjects, self.category_totals)
    
    def set_semester(self, semester):
        """Called when semester combo box changes"""
        self.current_semester = semester
        self.load_semester_data(semester)
    
    def calculate_progress_from_subjects(self, subjects, category_totals):
        """Calculate progress data dynamically from subjects"""
        # Count completed subjects by category
        category_counts = {}
        for subject in subjects:
            category = subject.get("category", "")
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Build categories list for progress data
        categories = []
        total_completed = 0
        total_required = 0
        
        for category_name, total in category_totals.items():
            completed = category_counts.get(category_name, 0)
            percentage = int((completed / total * 100)) if total > 0 else 0
            
            categories.append({
                "name": category_name,
                "completed": completed,
                "total": total,
                "percentage": percentage
            })
            
            total_completed += completed
            total_required += total
        
        # Calculate overall progress
        overall_progress = int((total_completed / total_required * 100)) if total_required > 0 else 0
        
        # Update progress data
        self.progress_data = {
            "overall_progress": overall_progress,
            "categories": categories
        }
        
        # Update charts
        self.update_charts()
    
    def on_file_changed(self, path):
        """Triggered when JSON file is modified"""
        print(f"🔄 Detected change in {path}, reloading...")
        
        if path == self.subjects_file_path:
            self.load_subjects_from_file()
        
        # Re-add the file watcher
        if os.path.exists(self.subjects_file_path):
            if self.subjects_file_path not in self.file_watcher.files():
                self.file_watcher.addPath(self.subjects_file_path)
    
    def update_charts(self):
        """Update both circular and bar charts"""
        self.plot_circular_progress()
        self.plot_horizontal_bars()
    
    def plot_circular_progress(self):
        """Draw the circular progress chart (donut chart)"""
        self.circular_ax.clear()
        
        overall_progress = self.progress_data.get("overall_progress", 0)
        
        # Create donut chart
        colors = ['#2c5530', '#E8E8E8']  # Dark green for progress, light gray for remaining
        sizes = [overall_progress, 100 - overall_progress]
        
        # Create the donut chart
        wedges, texts = self.circular_ax.pie(
            sizes,
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.3, edgecolor='white', linewidth=2)
        )
        
        # Add center text
        self.circular_ax.text(
            0, 0, f'{overall_progress}%',
            ha='center', va='center',
            fontsize=20, fontweight='bold',
            color='#2c5530', 
        )
        
        self.circular_ax.text(
            0, -0.25, 'Degree Progress',
            ha='center', va='center',
            fontsize=7, color='#666666',
        )
        
        self.circular_ax.set_aspect('equal')
        self.circular_canvas.draw()
    
    def plot_horizontal_bars(self):
        """Draw horizontal bar charts using seaborn"""
        self.bar_ax.clear()
        
        categories = self.progress_data.get("categories", [])
        
        if not categories:
            return
        
        # Prepare data for seaborn
        names = []
        percentages = []
        labels = []
        
        for cat in categories:
            names.append(cat['name'])
            percentages.append(cat['percentage'])
            labels.append(f"{cat['completed']} of {cat['total']} Progress")
        
        # Reverse order (top to bottom)
        names = names[::-1]
        percentages = percentages[::-1]
        labels = labels[::-1]
        
        # Create DataFrame for seaborn
        df = pd.DataFrame({
            'Category': names,
            'Percentage': percentages,
            'Remaining': [100 - p for p in percentages]
        })
        
        # Set seaborn style
        sns.set_style("whitegrid")
        
        # Plot the bars
        y_pos = range(len(names))
        
        # Plot completed portion (dark green)
        self.bar_ax.barh(y_pos, percentages, color='#2c5530', height=0.6, label='Completed')
        
        # Plot remaining portion (light gray)
        self.bar_ax.barh(y_pos, [100 - p for p in percentages], 
                        left=percentages, color='#E8E8E8', height=0.6, label='Remaining')
        
        # Add percentage labels on the bars
        for i, (pct, label) in enumerate(zip(percentages, labels)):
            # Percentage text
            self.bar_ax.text(pct / 2, i, f'{int(pct)}%', 
                           ha='center', va='center',
                           fontsize=6, fontweight='bold', color='white')
            
            # Progress label (e.g., "18 of 34 Progress")
            self.bar_ax.text(2, i - 0.35, label,
                           ha='left', va='center',
                           fontsize=5, color='#666666')
        
        # Customize the plot
        self.bar_ax.set_yticks(y_pos)
        self.bar_ax.set_yticklabels(names, fontsize=7, fontweight='bold')
        self.bar_ax.set_xlim(0, 100)
        self.bar_ax.set_xlabel('')
        self.bar_ax.set_xticks([])
        
        # Remove spines
        self.bar_ax.spines['top'].set_visible(False)
        self.bar_ax.spines['right'].set_visible(False)
        self.bar_ax.spines['bottom'].set_visible(False)
        self.bar_ax.spines['left'].set_visible(False)
        
        # Remove grid
        self.bar_ax.grid(False)
        
        # Adjust layout
        self.bar_canvas.figure.tight_layout()
        self.bar_canvas.draw()