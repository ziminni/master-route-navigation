from PyQt6.QtWidgets import QHeaderView, QWidget, QPushButton, QTableWidget, QTableWidgetItem
from PyQt6 import uic
try:
    from services.attendance_service import load_attendance
    from services.event_timeline_service import load_timeline
except Exception:
    load_attendance = lambda event_name=None: {"records": []}
    load_timeline = lambda: {"timeline": []}


def wire_org_officer_signals(window: object, ui_path_func) -> None:
    # Connect to the updated object name from UI: ViewAttendanceButton
    if hasattr(window, "ViewAttendanceButton"):
        window.ViewAttendanceButton.clicked.connect(lambda: _load_and_show_attendance(window, ui_path_func))

    # Fit various tables if present
    for table_name in [
        "PendingTable", "Events_table_3", "Events_table_4",
        "Events_table_6", "Events_table_7", "tableWidget",
        "EventT_Table", "Events_table"
    ]:
        table = getattr(window, table_name, None)
        if table and hasattr(table, "horizontalHeader"):
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            if hasattr(table, "resizeRowsToContents"):
                table.resizeRowsToContents()

    # Toggle Upcoming/Rejected in OrgOfficer UI stacked widget (UpcomingReschedule)
    stacked = getattr(window, "UpcomingReschedule", None)
    if stacked and hasattr(stacked, "setCurrentIndex"):
        # Buttons live on the pages; guard with hasattr
        if hasattr(window, "UpcomingButton_2"):
            window.UpcomingButton_2.clicked.connect(lambda: stacked.setCurrentIndex(0))
        if hasattr(window, "RejectedButton"):
            window.RejectedButton.clicked.connect(lambda: stacked.setCurrentIndex(1))


def wire_faculty_signals(window: object, open_timeline, open_reschedule, open_proposal) -> None:
    # Updated object names from UI: RequestEventProposalButton, RequestRescheduleButton
    if hasattr(window, "RequestEventProposalButton"):
        window.RequestEventProposalButton.clicked.connect(open_proposal)
    if hasattr(window, "RequestRescheduleButton"):
        window.RequestRescheduleButton.clicked.connect(open_reschedule)

    # Toggle left-side stacked widget (stackedWidget_2) with Upcoming/Rescheduled buttons
    left_stack = getattr(window, "stackedWidget_2", None)
    if left_stack and hasattr(left_stack, "setCurrentIndex"):
        if hasattr(window, "pushButton_8"):
            window.pushButton_8.clicked.connect(lambda: left_stack.setCurrentIndex(0))
        if hasattr(window, "pushButton_9"):
            window.pushButton_9.clicked.connect(lambda: left_stack.setCurrentIndex(1))

    # Toggle middle proposals stacked widget (stackedWidget_3) with Approved/Rejected buttons
    mid_stack = getattr(window, "stackedWidget_3", None)
    if mid_stack and hasattr(mid_stack, "setCurrentIndex"):
        if hasattr(window, "pushButton_17"):
            window.pushButton_17.clicked.connect(lambda: mid_stack.setCurrentIndex(0))
        if hasattr(window, "pushButton_18"):
            window.pushButton_18.clicked.connect(lambda: mid_stack.setCurrentIndex(1))


def _show_page(window: object, index: int) -> None:
    if hasattr(window, "stackedWidget"):
        window.stackedWidget.setCurrentIndex(index)


def _load_and_show_attendance(window: object, ui_path_func) -> None:
    # Lazy-load Attendance.ui into index 1 if not already present
    if not hasattr(window, "attendance_page") or window.attendance_page is None:
        attendance_widget = QWidget()
        uic.loadUi(ui_path_func("Attendance.ui"), attendance_widget)
        # If there is already a widget at index 1, replace it; otherwise insert
        if hasattr(window, "stackedWidget"):
            if window.stackedWidget.count() > 1:
                window.stackedWidget.removeWidget(window.stackedWidget.widget(1))
                window.stackedWidget.insertWidget(1, attendance_widget)
            else:
                window.stackedWidget.insertWidget(1, attendance_widget)
        window.attendance_page = attendance_widget
        # Wire Go Back button inside the newly loaded page
        go_back_btn = attendance_widget.findChild(QPushButton, "pushButton_4")
        if go_back_btn:
            go_back_btn.clicked.connect(lambda: _show_page(window, 0))

    _show_page(window, 1)

    # Populate table if present
    attendance_widget = getattr(window, "attendance_page", None)
    if attendance_widget:
        # Populate event and filter combos if available
        try:
            data = load_attendance()
        except Exception:
            data = {"records": []}
        combo_event = attendance_widget.findChild(QWidget, "comboBox")
        if combo_event and hasattr(combo_event, "clear") and hasattr(combo_event, "addItem"):
            try:
                combo_event.clear()
                ev = data.get("event") or "Event: Event Name"
                combo_event.addItem(ev)
            except Exception:
                pass
        combo_filter = attendance_widget.findChild(QWidget, "comboBox_2")
        if combo_filter and hasattr(combo_filter, "clear") and hasattr(combo_filter, "addItem"):
            try:
                combo_filter.clear()
                for f in (data.get("filters") or ["All"]):
                    combo_filter.addItem(f)
            except Exception:
                pass
        table = attendance_widget.findChild(QTableWidget, "tableWidget")
        if table:
            _populate_attendance_table(table)


def _populate_attendance_table(table: QTableWidget) -> None:
    data = load_attendance().get("records", [])
    headers = [
        "Student ID", "Name", "Year", "Section", "Course",
        "Gender/Sex", "Attendance Status", "Time IN", "Time OUT"
    ]
    table.setColumnCount(len(headers))
    for c, h in enumerate(headers):
        table.setHorizontalHeaderItem(c, QTableWidgetItem(h))
    table.setRowCount(len(data))
    for r, rec in enumerate(data):
        table.setItem(r, 0, QTableWidgetItem(rec.get("studentId", "")))
        table.setItem(r, 1, QTableWidgetItem(rec.get("name", "")))
        table.setItem(r, 2, QTableWidgetItem(rec.get("year", "")))
        table.setItem(r, 3, QTableWidgetItem(rec.get("section", "")))
        table.setItem(r, 4, QTableWidgetItem(rec.get("course", "")))
        table.setItem(r, 5, QTableWidgetItem(rec.get("gender", "")))
        table.setItem(r, 6, QTableWidgetItem(rec.get("status", "")))
        table.setItem(r, 7, QTableWidgetItem(str(rec.get("timeIn", ""))))
        table.setItem(r, 8, QTableWidgetItem(str(rec.get("timeOut", ""))))


