# gwastatistics.py
import os
import json
import matplotlib
matplotlib.use('QtAgg')  
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QFileSystemWatcher
import pandas as pd


class GwaStatisticsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.gwa_data = {}
        self.current_semester = None
        self.file_watcher = QFileSystemWatcher(self)

        self.file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "student_grades.json")

        self.init_ui()
        self.load_grades_and_calculate_gwa()

        # Watch for file changes
        if os.path.exists(self.file_path):
            self.file_watcher.addPath(self.file_path)
            self.file_watcher.fileChanged.connect(self.on_file_changed)

    # ---------------------------------------------------------
    def init_ui(self):
        """Initialize layout and chart canvas"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Chart frame
        chart_frame = QFrame()
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(0, 0, 0, 0)

        # Matplotlib figure and axis
        self.canvas = FigureCanvas(plt.Figure(figsize=(12, 6)))
        self.ax = self.canvas.figure.subplots()
        chart_layout.addWidget(self.canvas)

        main_layout.addWidget(chart_frame)
        self.setObjectName("gwaStatisticsWidget")

    # ---------------------------------------------------------
    def load_grades_and_calculate_gwa(self):
        """Load grades and compute GWA per semester"""
        if not os.path.exists(self.file_path):
            print(f"⚠️ File not found: {self.file_path}")
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            semesters_data = data.get("semesters", {})
            self.gwa_data.clear()

            for semester, sem_data in semesters_data.items():
                grades = sem_data.get("grades", [])
                gwa = self.calculate_gwa(grades)
                if gwa is not None:
                    self.gwa_data[semester] = gwa

            # Plot all GWA values
            self.plot_gwa_chart()

        except Exception as e:
            print(f"❌ Error reading student_grades.json: {e}")

    # ---------------------------------------------------------
    def calculate_gwa(self, grades):
        """Calculate GWA for one semester using finals or re-exam (passed only)"""
        total_units = 0
        total_points = 0

        for subject in grades:
            units = subject.get("units", 0)
            finals = subject.get("finals")
            re_exam = subject.get("re_exam")
            remarks = str(subject.get("remarks", "")).upper().strip()

            # Skip failed or invalid entries
            if remarks == "FAILED":
                continue

            # Prefer re-exam grade if available
            try:
                grade_value = float(re_exam) if re_exam not in ("", None) else float(finals)
                total_points += grade_value * units
                total_units += units
            except (TypeError, ValueError):
                continue

        if total_units == 0:
            return None
        return round(total_points / total_units, 2)

    # ---------------------------------------------------------
    def on_file_changed(self, path):
        """Reload data when JSON file changes"""
        print(f"🔄 Detected change in {path}, reloading GWA...")
        self.load_grades_and_calculate_gwa()

        # Re-add file watcher
        if os.path.exists(self.file_path) and self.file_path not in self.file_watcher.files():
            self.file_watcher.addPath(self.file_path)

    # ---------------------------------------------------------
    def set_semester(self, semester):
        """Update chart dynamically when semester combo changes"""
        self.current_semester = semester
        self.plot_gwa_chart()

    # ---------------------------------------------------------
    def plot_gwa_chart(self):
        """Draw the GWA per semester line chart (filtered if one semester selected)"""
        self.ax.clear()

        if not self.gwa_data:
            self.ax.text(0.5, 0.5, 'No GWA data available',
                         ha='center', va='center', transform=self.ax.transAxes,
                         fontsize=14, color='gray')
            self.canvas.draw()
            return

        # Filter data if a specific semester is selected
        if self.current_semester and self.current_semester in self.gwa_data:
            semesters = [self.current_semester]
            gwa_values = [self.gwa_data[self.current_semester]]
        else:
            semesters = sorted(self.gwa_data.keys())
            gwa_values = [self.gwa_data[s] for s in semesters]

        df = pd.DataFrame({"Semester": semesters, "GWA": gwa_values})

        # Seaborn styling
        sns.set_style("whitegrid")

        # Line chart
        sns.lineplot(
            data=df,
            x="Semester",
            y="GWA",
            marker="o",
            markersize=8,
            color="#1b4332",
            linewidth=2,
            ax=self.ax
        )

        # Invert Y-axis (lower GWA = better)
        self.ax.set_ylim(5, 1)
        self.ax.set_xlabel("")
        self.ax.set_ylabel("GWA", fontsize=12, fontweight='bold', color="#1b4332")

        # Format ticks
        self.ax.tick_params(axis="x", rotation=45, labelsize=9)
        self.ax.tick_params(axis="y", labelsize=10)

        # Light grid
        self.ax.grid(True, linestyle="-", linewidth=0.5, color="gray", alpha=0.3)
        self.ax.set_axisbelow(True)

        self.canvas.figure.tight_layout()
        self.canvas.draw()