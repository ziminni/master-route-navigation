from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import QTimer, Qt, QAbstractTableModel
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QCalendarWidget, QFileDialog
import os
import json
import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import openpyxl
from openpyxl.styles import Font

from typing import Dict, List
from ..Base.manager_base import ManagerBase
from ..Base.faculty_admin_base import FacultyAdminBase
from widgets.orgs_custom_widgets.dialogs import CreateOrgDialog
from ui.Organization.audit_logs_ui import Ui_audit_logs_widget
from ui.Organization.generate_reports_ui import Ui_generate_reports_widget

class AuditLogModel(QAbstractTableModel):
    """Model for displaying audit logs."""
    def __init__(self, data: List[Dict], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["Timestamp", "Actor", "Action", "Organization", "Subject", "Details"]

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        try:
            row_data = self._data[index.row()]
            col_name = self._headers[index.column()]
        except IndexError:
            return None
        
        if role == Qt.ItemDataRole.DisplayRole:
            value = row_data.get(col_name.lower())
            if col_name == "Timestamp":
                try:
                    dt = datetime.datetime.fromisoformat(value)
                    return dt.strftime("%Y-%m-%d %I:%M:%S %p")
                except (ValueError, TypeError):
                    return value
            return value
        
        if role == Qt.ItemDataRole.BackgroundRole:
            return QColor("#f6f8fa") if index.row() % 2 == 1 else QColor("white")

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

class Admin(ManagerBase, FacultyAdminBase):
    """
    Admin view. Inherits from ManagerBase (for management methods) and
    FacultyAdminBase (for the non-student UI layout).
    Adds admin-specific features like the admin menu, create button,
    audit logs, and report generation pages.
    
    MRO: Admin -> ManagerBase -> FacultyAdminBase -> OrganizationViewBase -> User
    """
    
    def __init__(self, admin_name: str):
        FacultyAdminBase.__init__(self, name=admin_name)
        ManagerBase.__init__(self)
        
        self.report_start_date: datetime.date | None = None
        self.report_end_date: datetime.date | None = None
        
        self.last_report_logs: List[Dict] = []
        self.last_report_data: List[Dict] = []
        self.last_report_org: str = ""
        self.last_report_type: str = ""
        self.last_report_header_text: str = ""
        
        self._setup_admin_menu()
        self._setup_create_button()
        
        self._setup_audit_logs_page()
        self._setup_generate_reports_page()
        
        self.ui.stacked_widget.currentChanged.connect(self._on_stack_changed)
        
        self.load_orgs()

    def showEvent(self, event):
        """Override showEvent to ensure proper initial positioning after the widget is shown."""
        super().showEvent(event)
        QTimer.singleShot(0, self._reposition_create_button)
    
    def _on_stack_changed(self, index: int) -> None:
        """Handle stacked widget changes to reposition floating buttons."""
        if index == 0:
            QTimer.singleShot(0, self._reposition_create_button)
    
    def _setup_admin_menu(self) -> None:
        """Set up the admin menu button with dropdown options beside the search bar."""
        self.menu_btn = QtWidgets.QPushButton(self.ui.landing_page)
        self.menu_btn.setStyleSheet("background-color: transparent;")
        self.menu_btn.setObjectName("menu_btn")
        self.menu_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.menu_btn.setText("")
        
        icon = QtGui.QIcon()
        
        menu_icon_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", "..",
            "assets", "organization", "icons", "menu.png"
        )

        icon.addPixmap(
            QtGui.QPixmap(menu_icon_path), 
            QtGui.QIcon.Mode.Normal, 
            QtGui.QIcon.State.Off
        )
        self.menu_btn.setIcon(icon)
        self.menu_btn.setIconSize(QtCore.QSize(30, 30))
        
        self.ui.horizontalLayout_2.addWidget(self.menu_btn)
        
        self.admin_menu = QtWidgets.QMenu(self)
        
        self.admin_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 5px 25px 5px 25px; 
                color: black;
                border-radius: 5px;
            }
            QMenu::item:selected {
                /* This is the hover/selection effect */
                background-color: #FDC601; /* Your project's yellow */
                color: #084924;        /* Your project's dark green */
            }
            QMenu::separator {
                height: 1px;
                background: #e0e0e0;
                margin: 5px 0px 5px 0px;
            }
        """)

        generate_reports_action = self.admin_menu.addAction("Generate Reports")
        generate_reports_action.triggered.connect(self._generate_reports)
        
        audit_logs_action = self.admin_menu.addAction("Audit Logs")
        audit_logs_action.triggered.connect(self._open_audit_logs)
        
        archive_action = self.admin_menu.addAction("Archive")
        archive_action.triggered.connect(self._open_archive)
        
        self.menu_btn.clicked.connect(self._show_admin_menu)
    
    def _show_admin_menu(self) -> None:
        """Display the admin dropdown menu."""
        button_pos = self.menu_btn.mapToGlobal(QtCore.QPoint(0, self.menu_btn.height()))
        self.admin_menu.exec(button_pos)
    
    def _setup_create_button(self) -> None:
        """Set up the create organization/branch button in the lower right."""
        self.create_btn = QtWidgets.QPushButton("+ Create Organization/Branch", self.ui.landing_page)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #FDC601;
                color: white;
                border-radius: 10px;
                padding: 15px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #084924;
            }
        """)
        self.create_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.create_btn.clicked.connect(self._create_organization)
        
        self._reposition_create_button()
        self.create_btn.raise_()

    def _reposition_create_button(self) -> None:
        """Helper to set the geometry of the create button based on landing_page size."""
        if hasattr(self, 'create_btn'):
            BUTTON_WIDTH = 260
            BUTTON_HEIGHT = 50
            MARGIN_RIGHT = 30
            MARGIN_BOTTOM = 70

            self.create_btn.setGeometry(
                self.ui.landing_page.width() - BUTTON_WIDTH - MARGIN_RIGHT,
                self.ui.landing_page.height() - BUTTON_HEIGHT - MARGIN_BOTTOM,
                BUTTON_WIDTH,
                BUTTON_HEIGHT
            )
            self.create_btn.raise_()

    def resizeEvent(self, event) -> None:
        """Handle resize events to reposition the create button."""
        super().resizeEvent(event)
        if self.ui.stacked_widget.currentIndex() == 0:
            self._reposition_create_button()
    
    def _setup_audit_logs_page(self) -> None:
        """Load the audit logs UI as a new stacked widget page."""
        self.audit_logs_page = QtWidgets.QWidget()
        self.audit_logs_ui = Ui_audit_logs_widget()
        self.audit_logs_ui.setupUi(self.audit_logs_page)
        
        self.no_logs_label = QtWidgets.QLabel("No logs.", self.audit_logs_ui.audit_table_container)
        self.no_logs_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.no_logs_label.setStyleSheet("font-size: 20px; color: #888;")
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.no_logs_label.setSizePolicy(sizePolicy)
        self.audit_logs_ui.verticalLayout_17.addWidget(self.no_logs_label)
        self.no_logs_label.hide()
        
        self.audit_logs_ui.audit_back_btn.clicked.connect(
            lambda: self.ui.stacked_widget.setCurrentIndex(0)
        )
        
        self.audit_logs_ui.audit_search_btn.clicked.connect(self._perform_audit_search)
        self.audit_logs_ui.audit_line_edit.returnPressed.connect(self._perform_audit_search)
        
        self.ui.stacked_widget.addWidget(self.audit_logs_page)
    
    def _setup_generate_reports_page(self) -> None:
        """Load the generate reports UI as a new stacked widget page."""
        self.reports_page = QtWidgets.QWidget()
        self.reports_ui = Ui_generate_reports_widget()
        self.reports_ui.setupUi(self.reports_page)
        
        self.reports_ui.report_preview_text = QtWidgets.QPlainTextEdit(self.reports_ui.preview_frame)
        self.reports_ui.report_preview_text.setReadOnly(True)
        self.reports_ui.report_preview_text.setStyleSheet("background-color: transparent; border: none; font-family: 'Courier New', monospace;")
        
        preview_layout = QtWidgets.QVBoxLayout(self.reports_ui.preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.addWidget(self.reports_ui.report_preview_text)
        
        self.reports_ui.back_btn_reports.clicked.connect(
            lambda: self.ui.stacked_widget.setCurrentIndex(0)
        )
        
        self.reports_ui.generate_report_btn.clicked.connect(self.generate_report)
        self.reports_ui.pushButton.clicked.connect(self._select_start_date)
        self.reports_ui.pushButton_2.clicked.connect(self._select_end_date)
        self.reports_ui.download_pdf_btn.clicked.connect(self._download_pdf)
        self.reports_ui.download_excel_btn.clicked.connect(self._download_excel)
        
        self.ui.stacked_widget.addWidget(self.reports_page)
        
    def _generate_reports(self) -> None:
        """Navigate to generate reports page."""
        self._populate_reports_orgs() 
        self.reports_ui.report_preview_text.clear()
        self.report_start_date = None
        self.report_end_date = None
        self.reports_ui.pushButton.setText("Start Date")
        self.reports_ui.pushButton_2.setText("End Date")
        
        self.last_report_logs = []
        self.last_report_data = []
        self.last_report_org = ""
        self.last_report_type = ""
        self.last_report_header_text = ""
        
        self.ui.stacked_widget.setCurrentIndex(4)

    def _open_audit_logs(self) -> None:
        """Navigate to audit logs page."""
        self.load_audit_logs_data()
        self.ui.stacked_widget.setCurrentIndex(3)

    def _open_archive(self) -> None:
        """Handle archive action."""
        QtWidgets.QMessageBox.information(
            self,
            "Archive",
            "Archive management feature will be implemented here."
        )
    
    def _create_organization(self) -> None:
        """Handle create organization/branch action."""
        from PyQt6.QtWidgets import QInputDialog
        
        items = ["Organization", "Branch"]
        item, ok = QInputDialog.getItem(
            self, 
            "Create", 
            "What would you like to create?", 
            items, 
            0, 
            False
        )
        
        if ok and item:
            is_branch = item == "Branch"
            dialog = CreateOrgDialog(self, is_branch=is_branch)
            dialog.exec()
            
            self.load_orgs() if not is_branch else self.load_branches()
            
    def _return_to_prev_page(self) -> None:
        """Navigate back, handling admin pages."""
        current_index = self.ui.stacked_widget.currentIndex()
        
        if current_index in [3, 4]:
            self.ui.stacked_widget.setCurrentIndex(0)
        else:
            super()._return_to_prev_page()
            
    def load_audit_logs_data(self, search_text: str = "") -> None:
        """Load and filter audit logs into the table."""
        print(f"Loading audit logs, searching for: {search_text}")
        
        logs = []
        try:
            if os.path.exists(self.audit_log_file):
                with open(self.audit_log_file, 'r') as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
        except Exception as e:
            print(f"Error loading audit log file: {str(e)}")
            logs = []

        filtered_logs = []
        if search_text:
            for log in logs:
                if any(search_text in str(val).lower() for val in log.values() if val):
                    filtered_logs.append(log)
        else:
            filtered_logs = logs
        
        filtered_logs.reverse()
        
        model = AuditLogModel(filtered_logs)
        self.audit_logs_ui.audit_table_view.setModel(model)
        
        self.audit_logs_ui.audit_table_view.setAlternatingRowColors(False)
        self.audit_logs_ui.audit_table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.audit_logs_ui.audit_table_view.horizontalHeader().setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.audit_logs_ui.audit_table_view.verticalHeader().setVisible(False)
        
        if not filtered_logs:
            self.audit_logs_ui.audit_table_view.hide()
            self.no_logs_label.show()
        else:
            self.audit_logs_ui.audit_table_view.show()
            self.no_logs_label.hide()

    def _perform_audit_search(self) -> None:
        """Handle audit logs search."""
        search_text = self.audit_logs_ui.audit_line_edit.text().strip().lower()
        self.load_audit_logs_data(search_text)

    def _populate_reports_orgs(self) -> None:
        """Populate organizations in the reports dropdown."""
        orgs = self._load_data()
        self.reports_ui.select_org_dd.clear()
        for org in orgs:
            if not org["is_branch"]:
                self.reports_ui.select_org_dd.addItem(org["name"])
                for branch in org.get("branches", []):
                    self.reports_ui.select_org_dd.addItem(f"  - {branch['name']}")

    def _create_calendar_dialog(self, current_date=None) -> tuple[QDialog, QCalendarWidget]:
        """Helper to create a modal calendar dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Date")
        layout = QVBoxLayout(dialog)
        calendar = QCalendarWidget(dialog)
        if current_date:
            calendar.setSelectedDate(QtCore.QDate(current_date))
        layout.addWidget(calendar)
        dialog.setLayout(layout)
        return dialog, calendar

    def _select_start_date(self) -> None:
        """Open a calendar to select the report start date."""
        dialog, calendar = self._create_calendar_dialog(self.report_start_date)
        
        def on_date_clicked(date):
            self.report_start_date = date.toPyDate()
            self.reports_ui.pushButton.setText(f"Start: {self.report_start_date.strftime('%Y-%m-%d')}")
            dialog.accept()

        calendar.clicked.connect(on_date_clicked)
        dialog.exec()

    def _select_end_date(self) -> None:
        """Open a calendar to select the report end date."""
        dialog, calendar = self._create_calendar_dialog(self.report_end_date)
        
        def on_date_clicked(date):
            self.report_end_date = date.toPyDate()
            self.reports_ui.pushButton_2.setText(f"End: {self.report_end_date.strftime('%Y-%m-%d')}")
            dialog.accept()

        calendar.clicked.connect(on_date_clicked)
        dialog.exec()

    def _generate_event_history_report(self, logs: List[Dict]) -> str:
        """Generates the body for the 'Event History' report."""
        if not logs:
            return "No activities found in this period."
        
        report_text = ""
        for log in sorted(logs, key=lambda x: x['timestamp']):
            dt = datetime.datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %I:%M %p')
            report_text += f"[{dt}] {log['actor']} performed {log['action']}.\n"
            report_text += f"    -> Subject: {log.get('subject', 'N/A')}\n"
            report_text += f"    -> Details: {log.get('details', 'N/A')}\n\n"
        return report_text

    def _generate_membership_report(self, logs: List[Dict]) -> str:
        """Generates the body for the 'Membership' report."""
        report_logs = [
            log for log in logs 
            if log["action"] in ["ACCEPT_APPLICANT", "KICK_MEMBER", "EDIT_MEMBER"]
        ]
        if not report_logs:
            return "No membership changes found in this period."
        
        report_text = ""
        for log in sorted(report_logs, key=lambda x: x['timestamp']):
            dt = datetime.datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %I:%M %p')
            report_text += f"[{dt}] {log['actor']} performed {log['action']} on {log['subject']}. \n    Details: {log['details']}\n"
        return report_text

    def _generate_officer_list_report(self, org_name: str) -> str:
        """
        Generates the body for the 'Officer List' report.
        Also caches the officer data in self.last_report_data.
        """
        report_text = "This report shows the CURRENT officer list and is not affected by the date range.\n\n"
        all_orgs = self._load_data()
        found_org = None
        for org in all_orgs:
            if org['name'] == org_name:
                found_org = org
                break
            for branch in org.get("branches", []):
                if branch['name'] == org_name:
                    found_org = branch
                    break
            if found_org:
                break
        
        if not found_org or not found_org.get("officers"):
            self.last_report_data = []
            return "No officers found for this organization."
        
        self.last_report_data = found_org.get("officers", [])
        for officer in self.last_report_data:
            report_text += f" - {officer.get('name', 'N/A'):<30} | {officer.get('position', 'N/A')}\n"
        return report_text

    def _generate_summary_report(self, logs: List[Dict]) -> str:
        """Generates the body for the 'Summary' report."""
        if not logs:
            return "No activities found in this period."
        
        actions = {}
        for log in logs:
            action_type = log.get('action', 'UNKNOWN')
            actions[action_type] = actions.get(action_type, 0) + 1
        
        report_text = "Summary of all actions in this period:\n\n"
        for action, count in sorted(actions.items()):
            report_text += f" - {action:<25} | {count} time(s)\n"
        return report_text

    # --- Main Report Generation Method ---
    
    def generate_report(self) -> None:
        """Generate report based on selections and display in preview."""
        org_name = self.reports_ui.select_org_dd.currentText().strip().lstrip("- ")
        report_type = self.reports_ui.report_type_dd.currentText()
        
        if org_name == "Select Organization":
            QMessageBox.warning(self, "Select Organization", "Please select an organization or branch.")
            return
            
        start_date = self.report_start_date
        end_date = self.report_end_date
        
        if start_date and end_date and start_date > end_date:
            QMessageBox.warning(self, "Invalid Date Range", "Start date must be before end date.")
            return
            
        date_range_str = "for all time"
        if start_date and end_date:
            date_range_str = f"from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        elif start_date:
            date_range_str = f"from {start_date.strftime('%Y-%m-%d')} onwards"
        elif end_date:
            date_range_str = f"up to {end_date.strftime('%Y-%m-%d')}"
        
        logs = []
        try:
            if os.path.exists(self.audit_log_file):
                with open(self.audit_log_file, 'r') as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
        except Exception as e:
            self.reports_ui.report_preview_text.setPlainText(f"Error loading audit logs: {e}")
            return

        org_logs = [log for log in logs if log.get("organization") == org_name]
        
        date_filtered_logs = []
        for log in org_logs:
            try:
                log_dt = datetime.datetime.fromisoformat(log['timestamp']).date()
                if start_date and log_dt < start_date:
                    continue
                if end_date and log_dt > end_date:
                    continue
                date_filtered_logs.append(log)
            except (ValueError, TypeError):
                continue
        
        report_text = f"Report Type: {report_type}\n"
        report_text += f"Organization/Branch: {org_name}\n"
        report_text += f"Date Range: {date_range_str}\n"
        report_text += f"Generated by: {self.name}\n"
        report_text += f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n"
        report_text += "=" * 50 + "\n\n"
        
        self.last_report_header_text = "\n".join(report_text.split('\n')[:6])
        
        body_text = ""
        if report_type == "Event History (Default)":
            body_text = self._generate_event_history_report(date_filtered_logs)
        elif report_type == "Membership":
            body_text = self._generate_membership_report(date_filtered_logs)
        elif report_type == "Officer List":
            body_text = self._generate_officer_list_report(org_name)
        elif report_type == "Summary":
            body_text = self._generate_summary_report(date_filtered_logs)
        else:
            body_text = f"Report type '{report_type}' is not yet implemented."
        
        self.reports_ui.report_preview_text.setPlainText(report_text + body_text)
        
        self.last_report_logs = date_filtered_logs
        self.last_report_org = org_name
        self.last_report_type = report_type

    def _download_pdf(self) -> None:
        """Saves the content of the report preview as a PDF."""
        report_text = self.reports_ui.report_preview_text.toPlainText()
        if not report_text:
            QMessageBox.warning(self, "Empty Report", "Cannot download an empty report. Please generate a report first.")
            return

        org_name = self.last_report_org
        report_type = self.last_report_type
        suggested_name = f"{org_name}_{report_type}_Report.pdf".replace(" ", "_").replace("/", "_")

        filename, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", suggested_name, "PDF Files (*.pdf)")
        
        if filename:
            try:
                doc = SimpleDocTemplate(filename, pagesize=letter)
                styles = getSampleStyleSheet()
                style_mono = styles['Code']
                
                formatted_text = report_text.replace('\n', '<br/>')
                
                story = [Paragraph(formatted_text, style_mono)]
                
                doc.build(story)
                QMessageBox.information(self, "Success", f"Report successfully saved to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save PDF: {str(e)}")

    
    def _write_excel_header(self, ws, row):
        """Writes the report header block to the worksheet."""
        header_lines = self.last_report_header_text.split('\n')
        bold_font = Font(bold=True)
        for line in header_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                ws.cell(row=row, column=1).value = key + ":"
                ws.cell(row=row, column=1).font = bold_font
                ws.cell(row=row, column=2).value = value.strip()
            else:
                ws.cell(row=row, column=1).value = line
            row += 1
        return row + 1

    def _auto_fit_excel_cols(self, ws):
        """Auto-fit all columns in the worksheet."""
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width

    def _download_excel(self) -> None:
        """Saves the generated report as a structured Excel file."""
        if not self.last_report_type:
            QMessageBox.warning(self, "Empty Report", "Cannot download an empty report. Please generate a report first.")
            return

        suggested_name = f"{self.last_report_org}_{self.last_report_type}_Report.xlsx".replace(" ", "_").replace("/", "_")
        filename, _ = QFileDialog.getSaveFileName(self, "Save Excel Report", suggested_name, "Excel Files (*.xlsx)")
        
        if not filename:
            return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Report"
            
            current_row = self._write_excel_header(ws, 1)
            
            bold_font = Font(bold=True)
            
            if self.last_report_type == "Officer List":
                ws.cell(row=current_row, column=1).value = "Name"
                ws.cell(row=current_row, column=1).font = bold_font
                ws.cell(row=current_row, column=2).value = "Position"
                ws.cell(row=current_row, column=2).font = bold_font
                current_row += 1
                
                if self.last_report_data:
                    for officer in self.last_report_data:
                        ws.cell(row=current_row, column=1).value = officer.get('name', 'N/A')
                        ws.cell(row=current_row, column=2).value = officer.get('position', 'N/A')
                        current_row += 1
                else:
                    ws.cell(row=current_row, column=1).value = "No officers found."

            elif self.last_report_type == "Summary":
                ws.cell(row=current_row, column=1).value = "Action"
                ws.cell(row=current_row, column=1).font = bold_font
                ws.cell(row=current_row, column=2).value = "Count"
                ws.cell(row=current_row, column=2).font = bold_font
                current_row += 1
                
                actions = {}
                for log in self.last_report_logs:
                    action_type = log.get('action', 'UNKNOWN')
                    actions[action_type] = actions.get(action_type, 0) + 1
                
                if not actions:
                    ws.cell(row=current_row, column=1).value = "No activities found."
                else:
                    for action, count in sorted(actions.items()):
                        ws.cell(row=current_row, column=1).value = action
                        ws.cell(row=current_row, column=2).value = count
                        current_row += 1
            
            else:
                headers = ["Timestamp", "Actor", "Action", "Subject", "Details"]
                for c, header in enumerate(headers, 1):
                    ws.cell(row=current_row, column=c).value = header
                    ws.cell(row=current_row, column=c).font = bold_font
                current_row += 1
                
                logs_to_write = self.last_report_logs
                if self.last_report_type == "Membership":
                    logs_to_write = [
                        log for log in self.last_report_logs
                        if log["action"] in ["ACCEPT_APPLICANT", "KICK_MEMBER", "EDIT_MEMBER"]
                    ]
                
                if not logs_to_write:
                    ws.cell(row=current_row, column=1).value = "No logs found for this report type."
                else:
                    for log in sorted(logs_to_write, key=lambda x: x['timestamp']):
                        try:
                            dt = datetime.datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %I:%M %p')
                        except (ValueError, TypeError):
                            dt = log.get('timestamp', 'N/A')
                            
                        ws.cell(row=current_row, column=1).value = dt
                        ws.cell(row=current_row, column=2).value = log.get('actor', 'N/A')
                        ws.cell(row=current_row, column=3).value = log.get('action', 'N/A')
                        ws.cell(row=current_row, column=4).value = log.get('subject', 'N/A')
                        ws.cell(row=current_row, column=5).value = log.get('details', 'N/A')
                        current_row += 1
            
            self._auto_fit_excel_cols(ws)
            wb.save(filename)
            QMessageBox.information(self, "Success", f"Report successfully saved to:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Excel file: {str(e)}")