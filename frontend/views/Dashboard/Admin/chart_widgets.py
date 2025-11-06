import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import numpy as np
import os


class ChartWidget(QWidget):
    """Base chart widget using matplotlib"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 6), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Set matplotlib style
        plt.style.use('default')

class TrendChart(ChartWidget):
    """Crypto-style trend chart for system usage"""
    def __init__(self, data_file, parent=None):
        super().__init__(parent)
        abs_data_file = data_file
        if not os.path.isabs(data_file):
            abs_data_file = os.path.join(os.path.dirname(__file__), data_file)
        self.load_and_plot(abs_data_file)
    
    def load_and_plot(self, data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            months = [item['month'] for item in data['data']]
            users = [item['users'] for item in data['data']]
            
            ax = self.figure.add_subplot(111)
            ax.clear()
            
            # Create trend line with gradient fill
            ax.plot(months, users, color='#3b82f6', linewidth=3, marker='o', markersize=6)
            ax.fill_between(months, users, alpha=0.3, color='#3b82f6')
            
            ax.set_title('Daily Active Users Over Time', fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Month', fontsize=12)
            ax.set_ylabel('Active Users', fontsize=12)
            
            # Style the chart
            ax.grid(True, alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            # Rotate x-axis labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error loading trend chart data: {e}")

class BarChart(ChartWidget):
    """Bar chart for engagement and house standings"""
    def __init__(self, data_file, chart_type="engagement", parent=None):
        super().__init__(parent)
        self.chart_type = chart_type
        abs_data_file = data_file
        if not os.path.isabs(data_file):
            abs_data_file = os.path.join(os.path.dirname(__file__), data_file)
        self.load_and_plot(abs_data_file)
    
    def load_and_plot(self, data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            ax = self.figure.add_subplot(111)
            ax.clear()
            
            if self.chart_type == "engagement":
                modules = [item['module'] for item in data['data']]
                engagement = [item['engagement'] for item in data['data']]
                
                bars = ax.bar(modules, engagement, color=['#10b981', '#3b82f6', '#f59e0b', '#ef4444'])
                ax.set_title('Engagement Across Academic Modules', fontsize=14, fontweight='bold', pad=20)
                ax.set_ylabel('Engagement Score (%)', fontsize=12)
                
                # Add value labels on bars
                for bar, value in zip(bars, engagement):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'{value}%', ha='center', va='bottom', fontweight='bold')
                
            elif self.chart_type == "house":
                houses = [item['house'] for item in data['data']]
                points = [item['points'] for item in data['data']]
                
                # Sort by points (Python should be leading)
                sorted_data = sorted(zip(houses, points), key=lambda x: x[1], reverse=True)
                houses, points = zip(*sorted_data)
                
                colors = ['#10b981' if 'Python' in house else '#3b82f6' if 'Java' in house else '#f59e0b' for house in houses]
                bars = ax.bar(houses, points, color=colors)
                
                ax.set_title('Current House Points Ranking', fontsize=14, fontweight='bold', pad=20)
                ax.set_ylabel('Points', fontsize=12)
                
                # Add value labels on bars
                for bar, value in zip(bars, points):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 50,
                           f'{value}', ha='center', va='bottom', fontweight='bold')
            
            # Style the chart
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            # Rotate x-axis labels if needed
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error loading bar chart data: {e}")

class PieChart(ChartWidget):
    """Pie chart for sentiment analysis"""
    def __init__(self, data_file, parent=None):
        super().__init__(parent)
        abs_data_file = data_file
        if not os.path.isabs(data_file):
            abs_data_file = os.path.join(os.path.dirname(__file__), data_file)
        self.load_and_plot(abs_data_file)
    
    def load_and_plot(self, data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            sentiments = [item['sentiment'] for item in data['data']]
            percentages = [item['percentage'] for item in data['data']]
            
            ax = self.figure.add_subplot(111)
            ax.clear()
            
            colors = ['#10b981', '#f59e0b', '#ef4444']  # Green, Yellow, Red
            wedges, texts, autotexts = ax.pie(percentages, labels=sentiments, colors=colors, 
                                            autopct='%1.1f%%', startangle=90, 
                                            textprops={'fontsize': 12, 'fontweight': 'bold'})
            
            ax.set_title('User Satisfaction Trends', fontsize=14, fontweight='bold', pad=20)
            
            # Make percentage text white and bold
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(11)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error loading pie chart data: {e}")

class BlankChart(ChartWidget):
    """Blank chart placeholder"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, f'{title}\n\nComing Soon!', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=16, color='#9ca3af',
                fontweight='bold')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        self.canvas.draw()
