import sys 
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QScrollArea, QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .metric_card import MetricCard, SpecialMetricCard
from .chart_card import ChartCard, InteractiveChartCard
from .chart_widgets import TrendChart, BarChart, PieChart, BlankChart


class NonClickableMetricCard(MetricCard):
    """ Non-clickable version of MetricCard for display-only metrics. """
    def __init__(self, title, value="", subtitle="", **kwargs):
        super().__init__(title, value, subtitle, **kwargs)
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mousePressEvent(self, event):
        pass
    def mouseReleaseEvent(self, event):
        pass


class DetailPage(QWidget):
    """Detailed page for each chart with full-size chart"""
    back_clicked = pyqtSignal()
    
    def __init__(self, title, chart_widget):
        super().__init__()
        
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Header with back button
        header_layout = QHBoxLayout()
        
        back_button = QPushButton("← Back to Dashboard")
        back_button.setFont(QFont("Arial", 12))
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
        """)
        back_button.clicked.connect(self.back_clicked.emit)
        
        header_layout.addWidget(back_button)
        header_layout.addStretch()
        
        page_title = QLabel(title)
        page_title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #111827; margin: 20px 0;")
        page_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(header_layout)
        layout.addWidget(page_title)
        
        # Chart area
        if chart_widget:
            layout.addWidget(chart_widget)
        else:
            placeholder = QLabel("Chart data will be displayed here")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #9ca3af; font-size: 16px;")
            layout.addWidget(placeholder)
        
        layout.addStretch()
        self.setLayout(layout)


class BlankPage(QWidget):
    back_clicked = pyqtSignal()
    
    def __init__(self, title):
        super().__init__()
        
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        
        page_title = QLabel(title)
        page_title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #111827; margin-bottom: 20px;")
        page_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        content = QLabel("Coming Soon!")
        content.setFont(QFont("Arial", 14))
        content.setStyleSheet("color: #6b7280;")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        back_button = QPushButton("← Back to Dashboard")
        back_button.setFont(QFont("Arial", 12))
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                margin-top: 20px;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
        """)
        back_button.clicked.connect(self.back_clicked.emit)
        
        layout.addWidget(page_title)
        layout.addWidget(content)
        layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        self.setLayout(layout)


class AdminDashboard(QWidget):
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        self.setWindowTitle("Admin Insights Dashboard")
        self.setGeometry(100, 100, 1200, 800)

        # Main layout for QWidget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.main_page = self.create_main_dashboard()
        self.stacked_widget.addWidget(self.main_page)

        self.metric_pages = {}
        self.chart_pages = {}

        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;   /* ✅ white dashboard */
            }
        """)

    def create_main_dashboard(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(32, 32, 32, 32)

        # --- Header ---
        header_layout = QVBoxLayout()
        title = QLabel("Admin Insights Dashboard")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827; margin-bottom: 4px;")

        subtitle = QLabel("Monitor V-Hub system performance, user engagement, and module analytics across CISC.")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #6b7280;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        # --- First row ---
        first_row_label = QLabel("Performance Metrics")
        first_row_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        first_row_label.setStyleSheet("color: #111827; margin-bottom: 8px;")
        main_layout.addWidget(first_row_label)

        scroll_area_row1 = QScrollArea()
        scroll_area_row1.setFixedHeight(150)
        scroll_area_row1.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area_row1.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area_row1.setWidgetResizable(True)
        
        scroll_widget_row1 = QWidget()
        scroll_widget_row1.setStyleSheet("background-color: #ffffff;") 
        scroll_layout_row1 = QHBoxLayout()
        scroll_layout_row1.setSpacing(16)
        scroll_layout_row1.setContentsMargins(0, 0, 0, 0)

        # --- First row ---
        metrics = [
            {"title": "Document Downloads", "value": "3,892", "subtitle": "↑ 8% from yesterday"},
            {"title": "Feedback Submissions", "value": "156", "subtitle": "↓ 3% from last week"},
            {"title": "Faculty Consultations", "value": "89", "subtitle": "Scheduled this week"},
            {"title": "Module Completion Rate", "value": "94.2%", "subtitle": "↑ 1.5% from last month"},
            {"title": "Average Session Time", "value": "24 min", "subtitle": "↑ 3 min from last week"},
            {"title": "Resource Utilization", "value": "78.5%", "subtitle": "Server capacity usage"},
        ]
        for config in metrics:
            card = MetricCard(config["title"], config["value"], config["subtitle"])
            card.clicked.connect(self.show_metric_page)
            scroll_layout_row1.addWidget(card)

        scroll_layout_row1.addStretch()
        scroll_widget_row1.setLayout(scroll_layout_row1)
        scroll_area_row1.setWidget(scroll_widget_row1)
        
        scroll_area_row1.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QScrollBar:horizontal {
                background: #ffffff;
                height: 8px;
                margin: 2px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #d1d5db;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover { background: #9ca3af; }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal { width: 0px; }
        """)
        main_layout.addWidget(scroll_area_row1)

        # --- Second row ---
        second_row_label = QLabel("System Overview")
        second_row_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        second_row_label.setStyleSheet("color: #111827; margin-bottom: 8px; margin-top: 16px;")
        main_layout.addWidget(second_row_label)

        fixed_row_layout = QHBoxLayout()
        fixed_row_layout.setSpacing(16)

        fixed_metrics = [
            {"title": "Most Active Module", "value": "CISC 101", "subtitle": "Desktop Application Development"},
            {"title": "System Uptime", "value": "99.8%", "subtitle": "Last 30 days"},
            {"title": "Total Active Users", "value": "1,247", "subtitle": "↑ 12% from last week"},
            {"title": "Active Organizations", "value": "23", "subtitle": "All departments online"},
            {"title": "System Engagement Rate", "value": "87.3%", "subtitle": "↑ 2.1% from last month"},
        ]

        for config in fixed_metrics:
            card = NonClickableMetricCard(config["title"], config["value"], config["subtitle"])
            card.setCursor(Qt.CursorShape.ArrowCursor)
            card.mousePressEvent = lambda event: None
            card.mouseReleaseEvent = lambda event: None
            fixed_row_layout.addWidget(card)

        main_layout.addLayout(fixed_row_layout)

        # --- Chart Grid ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                background: #ffffff;
                width: 8px;
                margin: 2px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #9ca3af; }
            QScrollBar::add-line:vertical { height: 0px; }
            QScrollBar:horizontal {
                background: #ffffff;
                height: 8px;
                margin: 2px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #d1d5db;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover { background: #9ca3af; }
            QScrollBar::add-line:horizontal { width: 0px; }
        """)

        container = QWidget()
        container.setStyleSheet("background-color: #ffffff;")
        grid = QGridLayout()
        grid.setSpacing(16)

        usage_chart = ChartCard("System Usage Trends", "Daily active users over time")
        usage_chart_widget = TrendChart("data/system_usage_trends.json")
        usage_chart.set_chart_content(usage_chart_widget)
        
        engagement_chart = ChartCard("Student Engagement Analytics", "Engagement across academic modules")
        engagement_chart_widget = BarChart("data/student_engagement.json", "engagement")
        engagement_chart.set_chart_content(engagement_chart_widget)
        
        feedback_table = ChartCard("Feedback Sentiment Analysis", "User satisfaction trends", show_actions=True)
        feedback_chart_widget = PieChart("data/feedback_sentiment.json")
        feedback_table.set_chart_content(feedback_chart_widget)
        
        events_table = ChartCard("Upcoming Events & Deadlines", "Organization events and academic calendar")
        events_chart_widget = BlankChart("Upcoming Events & Deadlines")
        events_table.set_chart_content(events_chart_widget)
        
        activity_table = ChartCard("Recent System Activity", "Live activity feed and notifications")
        activity_chart_widget = BlankChart("Recent System Activity")
        activity_table.set_chart_content(activity_chart_widget)
        
        house_table = ChartCard("House Standings & Performance", "Current house points ranking", show_actions=True)
        house_chart_widget = BarChart("data/house_standings.json", "house")
        house_table.set_chart_content(house_chart_widget)

        for card in [usage_chart, engagement_chart, feedback_table, events_table, activity_table, house_table]:
            card.clicked.connect(self.show_chart_page)

        for card in [feedback_table, house_table]:
            card.action_clicked.connect(self.handle_chart_action)

        grid.addWidget(usage_chart, 0, 0)
        grid.addWidget(engagement_chart, 0, 1)
        grid.addWidget(feedback_table, 0, 2)
        grid.addWidget(events_table, 1, 0)
        grid.addWidget(activity_table, 1, 1)
        grid.addWidget(house_table, 1, 2)

        container.setLayout(grid)
        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

        main_widget.setLayout(main_layout)
        return main_widget

    def show_metric_page(self, title):
        if title not in self.metric_pages:
            page = BlankPage(title)
            page.back_clicked.connect(self.show_main_dashboard)
            self.metric_pages[title] = page
            self.stacked_widget.addWidget(page)
        self.stacked_widget.setCurrentWidget(self.metric_pages[title])
    
    def show_chart_page(self, title):
        """Show detailed chart page when chart card is clicked"""
        if title not in self.chart_pages:
            # Create appropriate chart widget for the detail page
            chart_widget = None
            if title == "System Usage Trends":
                chart_widget = TrendChart("data/system_usage_trends.json")
            elif title == "Student Engagement Analytics":
                chart_widget = BarChart("data/student_engagement.json", "engagement")
            elif title == "Feedback Sentiment Analysis":
                chart_widget = PieChart("data/feedback_sentiment.json")
            elif title == "House Standings & Performance":
                chart_widget = BarChart("data/house_standings.json", "house")
            else:
                chart_widget = BlankChart(title)
            
            page = DetailPage(title, chart_widget)
            page.back_clicked.connect(self.show_main_dashboard)
            self.chart_pages[title] = page
            self.stacked_widget.addWidget(page)
        
        self.stacked_widget.setCurrentWidget(self.chart_pages[title])
    
    def show_main_dashboard(self):
        self.stacked_widget.setCurrentWidget(self.main_page)
    
    def handle_chart_action(self, chart_title, action_name):
        print(f"Action '{action_name}' clicked on chart '{chart_title}'")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    dashboard = AdminDashboard()
    dashboard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
