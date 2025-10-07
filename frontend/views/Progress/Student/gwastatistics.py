# gwastatistics.py
import os
import json
import matplotlib
matplotlib.use('Qt5Agg')
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QFileSystemWatcher
import pandas as pd


class GwaStatisticsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.gwa_data = {}
        self.file_watcher = QFileSystemWatcher(self)
        
        self.file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "grades.json")
        
        self.init_ui()
        self.load_grades_and_calculate_gwa()
        
        # Start watching the file
        if os.path.exists(self.file_path):
            self.file_watcher.addPath(self.file_path)
            self.file_watcher.fileChanged.connect(self.on_file_changed)

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Chart content
        chart_frame = self.create_chart()
        main_layout.addWidget(chart_frame)

        # Set object names for styling
        self.setObjectName("gwaStatisticsWidget")

    def create_chart(self):
        """Create the Seaborn GWA line chart"""
        frame = QFrame()
        layout = QVBoxLayout(frame)

        # Matplotlib Figure
        self.canvas = FigureCanvas(plt.Figure(figsize=(12, 6)))
        layout.addWidget(self.canvas)

        self.ax = self.canvas.figure.subplots()
        
        return frame
    
    def load_grades_and_calculate_gwa(self):
        """Load grades from JSON and calculate GWA per semester"""
        if not os.path.exists(self.file_path):
            print(f"⚠️ File not found: {self.file_path}")
            return
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            semesters_data = data.get("semesters", {})
            self.gwa_data = {}
            
            # Calculate GWA for each semester
            for semester, sem_data in semesters_data.items():
                grades = sem_data.get("grades", [])
                gwa = self.calculate_gwa(grades)
                if gwa is not None:
                    self.gwa_data[semester] = gwa
            
            # Plot the chart
            self.plot_gwa_chart()
            
        except Exception as e:
            print(f"❌ Error reading grades.json: {e}")
    
    def calculate_gwa(self, grades):
        """Calculate GWA from grades list"""
        total_units = 0
        total_grade_points = 0
        
        for grade in grades:
            units = grade.get("units", 0)
            finals = grade.get("finals", "")
            
            # Skip if finals is not a valid number
            try:
                final_grade = float(finals)
                total_units += units
                total_grade_points += final_grade * units
            except (ValueError, TypeError):
                continue
        
        if total_units == 0:
            return None
        
        return round(total_grade_points / total_units, 2)
    
    def on_file_changed(self, path):
        """Triggered when grades.json is modified"""
        print(f"🔄 Detected change in {path}, reloading GWA...")
        self.load_grades_and_calculate_gwa()
        
        # Re-add the file watcher
        if os.path.exists(self.file_path):
            if self.file_path not in self.file_watcher.files():
                self.file_watcher.addPath(self.file_path)

    def plot_gwa_chart(self):
        """Draw the GWA per semester line chart using seaborn"""
        self.ax.clear()
        
        if not self.gwa_data:
            self.ax.text(0.5, 0.5, 'No GWA data available', 
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=14, color='gray')
            self.canvas.draw()
            return
        
        # Sort semesters chronologically
        sorted_semesters = sorted(self.gwa_data.keys())
        semesters = sorted_semesters
        gwa_values = [self.gwa_data[sem] for sem in sorted_semesters]
        
        # Create DataFrame
        df = pd.DataFrame({"Semester": semesters, "GWA": gwa_values})
        
        # Set seaborn style
        sns.set_style("whitegrid")
        
        # Create line plot with markers
        sns.lineplot(
            data=df,
            x="Semester",
            y="GWA",
            marker="o",
            markersize=8,
            color="black",
            linewidth=2,
            ax=self.ax
        )
        
        # Customize the plot to match the image
        self.ax.set_ylim(5, 1)  # Inverted y-axis (lower GWA is better)
        self.ax.set_xlabel("")
        self.ax.set_ylabel("GWA", fontsize=12, fontweight='bold')
        
        # Rotate x-axis labels
        self.ax.tick_params(axis="x", rotation=45, labelsize=9)
        self.ax.tick_params(axis="y", labelsize=10)
        
        # Add grid lines
        self.ax.grid(True, which="major", linestyle="-", linewidth=0.5, color="gray", alpha=0.3)
        self.ax.set_axisbelow(True)
        
        # Adjust layout to prevent label cutoff
        self.canvas.figure.tight_layout()
        
        self.canvas.draw()
