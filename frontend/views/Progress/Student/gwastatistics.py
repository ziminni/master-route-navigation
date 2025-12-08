# frontend/views/Progress/Student/gwastatistics.py
import threading
import traceback
import requests

import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
import seaborn as sns

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot


class GwaStatisticsWidget(QWidget):
    """
    Thread-safe GWA widget. Shows ALL semesters regardless of current selection.
    Excluded from semester/year switching.
    """
    gwa_data_loaded = pyqtSignal(dict)  # emits { semester_key: gwa_value }

    def __init__(self, token=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.token = token or ""
        self.api_base = api_base.rstrip("/")

        self.gwa_data = {}           # { semester_key: gwa_value }
        self.semester_order = []     # Maintain chronological order

        self.file_lock = threading.Lock()

        self.init_ui()

        # connect signal then start worker
        self.gwa_data_loaded.connect(self._on_backend_data_slot)
        self.load_gwa_from_backend_async()

    # ---------------------------------------------------------
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        chart_frame = QFrame()
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(0, 0, 0, 0)

        self.canvas = FigureCanvas(plt.Figure(figsize=(12, 6)))
        self.ax = self.canvas.figure.subplots()
        chart_layout.addWidget(self.canvas)

        main_layout.addWidget(chart_frame)
        self.setObjectName("gwaStatisticsWidget")

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
    def load_gwa_from_backend_async(self):
        """
        GET /api/progress/student/gwa/ - Use dedicated GWA endpoint
        """
        url = f"{self.api_base}/api/progress/student/gwa/"
        headers = self._build_headers()

        def fetch():
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    # Backend returns {"semesters": {"2024-2025 – first": 1.75, ...}}
                    if isinstance(data, dict) and "semesters" in data:
                        gwa_map = data.get("semesters", {})
                        self.gwa_data_loaded.emit(gwa_map)
                    else:
                        self.gwa_data_loaded.emit({})
                else:
                    self.gwa_data_loaded.emit({})
            except Exception:
                traceback.print_exc()
                self.gwa_data_loaded.emit({})

        threading.Thread(target=fetch, daemon=True).start()

    # ---------------------------------------------------------
    @pyqtSlot(dict)
    def _on_backend_data_slot(self, gwa_map):
        with self.file_lock:
            self.gwa_data.clear()
            if isinstance(gwa_map, dict):
                self.gwa_data.update(gwa_map)
        
        # Sort semesters chronologically
        self._sort_semesters_chronologically()
        self.plot_gwa_chart()

    # ---------------------------------------------------------
    def _sort_semesters_chronologically(self):
        """Sort semesters in chronological order (Year 1, Sem 1 -> Year 4, Sem 2)"""
        if not self.gwa_data:
            self.semester_order = []
            return
            
        # Extract and sort semesters
        semesters = list(self.gwa_data.keys())
        
        # Custom sort function to handle "YYYY-YYYY – term" format
        def semester_sort_key(sem):
            try:
                # Split into year and term parts
                if ' – ' in sem:
                    year_part, term_part = sem.split(' – ', 1)
                elif ' - ' in sem:
                    year_part, term_part = sem.split(' - ', 1)
                else:
                    year_part, term_part = sem, ""
                
                # Extract start year
                start_year = int(year_part.split('-')[0]) if '-' in year_part else 0
                
                # Assign weight to term
                term_weight = 0
                term_lower = term_part.lower()
                if 'first' in term_lower or '1' in term_part:
                    term_weight = 1
                elif 'second' in term_lower or '2' in term_part:
                    term_weight = 2
                
                return (start_year, term_weight)
            except:
                return (0, 0)
        
        self.semester_order = sorted(semesters, key=semester_sort_key)

    # ---------------------------------------------------------
    def plot_gwa_chart(self):
        self.ax.clear()

        if not self.gwa_data:
            self.ax.text(
                0.5, 0.5, 'No GWA data available',
                ha='center', va='center', transform=self.ax.transAxes,
                fontsize=14, color='gray'
            )
            self.canvas.draw()
            return

        # ALWAYS show ALL semesters
        semesters = self.semester_order
        gwa_values = [self.gwa_data[s] for s in semesters]

        sns.set_style("whitegrid")

        # Plot the GWA data - line connecting all semesters
        self.ax.plot(
            range(len(semesters)),  # Use numeric positions for x-axis
            gwa_values,
            marker="o",  # Dot for each semester
            markersize=8,
            linewidth=2,
            color='#3498db'
        )

        # Set x-axis labels to semester names
        self.ax.set_xticks(range(len(semesters)))
        self.ax.set_xticklabels(semesters, rotation=45, ha='right', fontsize=9)

        # Set y-axis limits - FIXED: 1.0 at top, 5.0 at bottom
        if gwa_values:
            max_val = max(gwa_values)
            min_val = min(gwa_values)
            
            # Add padding
            padding = (max_val - min_val) * 0.1 if max_val > min_val else 0.5
            
            # For GWA: 1.0 (best) at TOP, 5.0 (worst) at BOTTOM
            # We need to invert the y-axis
            y_bottom = max(1.0, min_val - padding)  # This is actually the TOP visually
            y_top = min(5.0, max_val + padding)     # This is actually the BOTTOM visually
            
            # Set the limits (but we'll invert the axis)
            self.ax.set_ylim(y_top, y_bottom)  # Note: y_top is lower value, y_bottom is higher value
            
            # Add threshold lines
            self.ax.axhline(y=3.0, color='orange', linestyle=':', alpha=0.5, linewidth=1)
            self.ax.text(len(semesters)-0.5, 3.02, 'Passing (3.0)', 
                       fontsize=9, color='orange', alpha=0.7, ha='right')
            
            self.ax.axhline(y=4.0, color='red', linestyle=':', alpha=0.5, linewidth=1)
            self.ax.text(len(semesters)-0.5, 4.02, 'Failing (4.0+)', 
                       fontsize=9, color='red', alpha=0.7, ha='right')
            
            # Mark the best possible GWA
            self.ax.axhline(y=1.0, color='green', linestyle=':', alpha=0.5, linewidth=1)
            self.ax.text(len(semesters)-0.5, 1.02, 'Excellent (1.0)', 
                       fontsize=9, color='green', alpha=0.7, ha='right')
            
        else:
            # Default range if no data
            self.ax.set_ylim(5.0, 1.0)  # Inverted: 1 at top, 5 at bottom

        self.ax.set_xlabel("Semester", fontsize=10)
        self.ax.set_ylabel("GWA", fontsize=12, fontweight='bold')
        self.ax.set_title("General Weighted Average (GWA)", fontsize=14, fontweight='bold')

        self.ax.tick_params(axis="y", labelsize=10)
        self.ax.grid(True, linestyle="-", linewidth=0.5, alpha=0.3)
        self.ax.set_axisbelow(True)

        # Add value labels on points
        for i, (sem, val) in enumerate(zip(semesters, gwa_values)):
            # Position labels differently based on value
            vertical_offset = 15 if val <= 3.0 else -15
            
            self.ax.annotate(f'{val:.2f}', 
                           xy=(i, val), 
                           xytext=(0, vertical_offset),
                           textcoords='offset points',
                           ha='center',
                           fontsize=9,
                           fontweight='bold',
                           color='red' if val >= 4.0 else 'orange' if val >= 3.0 else 'green')

        self.canvas.figure.tight_layout()
        self.canvas.draw()

    # ---------------------------------------------------------
    def refresh_data(self):
        """Public method to refresh GWA data"""
        self.load_gwa_from_backend_async()