from PyQt6.QtWidgets import QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem
from datetime import datetime

# Services
try:
    from services.schedule_service import load_schedule
    from services.curriculum_service import load_curriculum
    from services.students_service import get_student_year
except Exception:
    load_schedule = lambda student_id=None: {}
    load_curriculum = lambda year_name=None: {}
    get_student_year = lambda student_id=None: None

    student_id = None #added this to hold the student id for use in other functions, gets the student id outside
     #added this to determine if the user is searching or not

def wire_schedule_signals(window: object) -> None:
    # Button connections
    if hasattr(window, "viewCurriculum"):
        try:
            if hasattr(window, "show_curriculum_page"):
                window.viewCurriculum.clicked.connect(window.show_curriculum_page)
            else:
                window.viewCurriculum.clicked.connect(lambda: _show_curriculum_page(window))
        except Exception:
            pass
    if hasattr(window, "Return"):
        try:
            if hasattr(window, "show_schedule_page"):
                window.Return.clicked.connect(window.show_schedule_page)
            else:
                window.Return.clicked.connect(lambda: _show_schedule_page(window))
        except Exception:
            pass

    # Search and semester change
    if hasattr(window, "Search") and hasattr(window, "StudentSearch"):
        # Hide search for students
        role = getattr(window, "user_role", "faculty")
        if role == "student":
            try:
                window.Search.setVisible(False)
                window.StudentSearch.setVisible(False)
            except Exception:
                pass
        else:
            window.Search.clicked.connect(lambda: _populate_schedule(window))
    if hasattr(window, "Semester"):


#Semester change
        try:
            window.Semester.currentIndexChanged.connect(lambda _=None: _populate_schedule(window))# This fixes the issue of thhe weekly table not updating on semester change
        except Exception:
            pass
        
        
        
        
    if hasattr(window, "YearBox"):
        try:
            window.YearBox.currentIndexChanged.connect(lambda _=None: _populate_curriculum(window))
        except Exception:
            pass
#consider putting some if statement here because it fires off regardless.
    # Initial populate
    _restrict_years(window)
    _populate_schedule(window)

    # Optional: ensure stacked widget navigation exists
    if hasattr(window, "stackedWidget") and isinstance(window.stackedWidget, QStackedWidget):
        pass


# --- Helpers ---
def _show_curriculum_page(window: object) -> None:
    try:
        if hasattr(window, "stackedWidget"):
            window.stackedWidget.setCurrentIndex(1)
    except Exception:
        pass


def _show_schedule_page(window: object) -> None:
    try:
        if hasattr(window, "stackedWidget"):
            window.stackedWidget.setCurrentIndex(0)
    except Exception:
        pass


_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
_TIMES_DISPLAY = [
    "7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM",
    "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM",
    "5:00 PM", "6:00 PM", "7:00 PM",
]
searching = False

def _format_time_display(hhmm: str) -> str:
    try:
        dt = datetime.strptime(hhmm, "%H:%M")
        return dt.strftime("%#I:%M %p") if hasattr(datetime, "strftime") else dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return hhmm








def _populate_schedule(window: object) -> None:
    student_id = None
    role = getattr(window, "user_role", "faculty")
    # Students: use their own id from attribute if provided; Faculty: use search box
    if role == "student":
        student_id = getattr(window, "student_id", None)
    else:
        student_id = getattr(window, "StudentSearch").text() if hasattr(window, "StudentSearch") else None
        
    data = load_schedule(student_id)
    _populate_weekly_table(getattr(window, "WeekTable_2", None), data, window)
    _populate_today(window, student_id) #added student_id to refer to the current user
    # If faculty searched for a student, restrict YearBox to that student's year
    try:
        _restrict_years(window)
    except Exception:
        pass
    _populate_curriculum(window)


def _populate_weekly_table(table: QTableWidget | None, schedule: dict, window) -> None:
    if not table or not isinstance(table, QTableWidget):
        return
    # Ensure table has expected dimensions (rows follow _TIMES_DISPLAY, columns follow _DAYS)
    table.setRowCount(len(_TIMES_DISPLAY))
    table.setColumnCount(len(_DAYS))
    for r, label in enumerate(_TIMES_DISPLAY):
        item = QTableWidgetItem(label)
        table.setVerticalHeaderItem(r, item)
    for c, day in enumerate(_DAYS):
        item = QTableWidgetItem(day)
        table.setHorizontalHeaderItem(c, item)

    sem_widj = getattr(window,"Semester", None)
    print (f"MODULE 3 WEEKLY SEMESTER SELECTED: ", sem_widj.currentText())
    semester = sem_widj.currentText()
    
    
    weekly = schedule.get(semester, {}).get("weekly",{}) if isinstance(schedule, dict) else {}
    # Clear cells
    for r in range(len(_TIMES_DISPLAY)):
        for c in range(len(_DAYS)):
            table.setItem(r, c, QTableWidgetItem(""))

    # Fill
    for day, entries in weekly.items():
        if day not in _DAYS:
            continue
        c = _DAYS.index(day)
        for entry in entries:
            time_disp = _format_time_display(entry.get("time", ""))
            if time_disp not in _TIMES_DISPLAY:
                continue
            r = _TIMES_DISPLAY.index(time_disp)
            text = f"{entry.get('subject', '')} ({entry.get('room', '')})"
            table.setItem(r, c, QTableWidgetItem(text))


def _populate_today(window: object, student_id) -> None:
    table = getattr(window, "tableWidget_2", None)
    if not table or not isinstance(table, QTableWidget):
        return
    schedule = load_schedule(getattr(window, "StudentSearch").text() if hasattr(window, "StudentSearch") else None)
    #This is the key fix VVV
    searching = hasattr(window, "StudentSearch") and window.StudentSearch.isVisible() and window.StudentSearch.text().strip() != ""
    # today = schedule.get("today", []) if isinstance(schedule, dict) else []#This should still refer to the weekly schedule json block, not a separate today
    #user schedules are selected
    #get date today
    daytoday = datetime.now().strftime("%A")
    #Specify selection of schedule json block using the student id and the day today
    
    sem_widj = getattr(window,"Semester", None) #This is the el fixo of the semester selection
    print (f"MODULE 3 TODAY SEMESTER SELECTED: ", sem_widj.currentText())
    semester = sem_widj.currentText()
    if not searching:
        student_id = getattr(window, "student_id", None)
        getusersched = schedule['schedules'][student_id][semester]['weekly'][daytoday]if student_id in schedule['schedules'] else []
    else:
        student_id = window.StudentSearch.text().strip()
        getusersched =schedule.get(semester, {}).get('weekly', {}).get(daytoday, []) if isinstance(schedule, dict) else []
        # getusersched = schedule[semester]['weekly'][daytoday]
    searching=False
    
    #select the json block of that day of week using the selected parameters
    # Mirror _TIMES_DISPLAY rows
    table.setRowCount(len(_TIMES_DISPLAY))
    table.setColumnCount(1)
    for r, label in enumerate(_TIMES_DISPLAY):
        item = QTableWidgetItem(label)
        table.setVerticalHeaderItem(r, item)
        table.setItem(r, 0, QTableWidgetItem(""))
    for entry in getusersched:
        time_disp = _format_time_display(entry.get("time", ""))
        if time_disp in _TIMES_DISPLAY:
            r = _TIMES_DISPLAY.index(time_disp)
            text = f"{entry.get('subject', '')} ({entry.get('room', '')})"
            table.setItem(r, 0, QTableWidgetItem(text))


def _populate_curriculum(window: object) -> None:
    year_name = None
    if hasattr(window, "YearBox") and hasattr(window.YearBox, "currentText"):
        year_name = window.YearBox.currentText()
    cur = load_curriculum(year_name)
    sem1 = getattr(window, "sem1", None)
    sem2 = getattr(window, "sem2frame", None)
    if not (isinstance(sem1, QTableWidget) and isinstance(sem2, QTableWidget)):
        return
    semesters = cur.get("semesters", []) if isinstance(cur, dict) else []
    _fill_semester_table(sem1, next((s for s in semesters if s.get("name") == "1st Semester"), {"subjects": []}))
    _fill_semester_table(sem2, next((s for s in semesters if s.get("name") == "2nd Semester"), {"subjects": []}))


def _fill_semester_table(table: QTableWidget, sem: dict) -> None:
    headers = ["Codes", "Subject Title", "Grades", "Units", "Pre-requisite(s)"]
    table.setColumnCount(len(headers))
    for c, h in enumerate(headers):
        table.setHorizontalHeaderItem(c, QTableWidgetItem(h))
    subjects = sem.get("subjects", [])
    table.setRowCount(len(subjects))
    for r, subj in enumerate(subjects):
        table.setItem(r, 0, QTableWidgetItem(subj.get("code", "")))
        table.setItem(r, 1, QTableWidgetItem(subj.get("title", "")))
        table.setItem(r, 2, QTableWidgetItem(str(subj.get("grade", ""))))
        table.setItem(r, 3, QTableWidgetItem(str(subj.get("units", ""))))
        prereq = ", ".join(subj.get("prerequisites", []) or [])
        table.setItem(r, 4, QTableWidgetItem(prereq))


def _restrict_years(window: object) -> None:
    role = getattr(window, "user_role", "faculty")
    box = getattr(window, "YearBox", None)
    if not box or not hasattr(box, "count"):
        return
    # Determine which student id to use for restriction:
    # - If the current UI is a student, use its student_id attribute
    # - Otherwise (faculty), if a StudentSearch is visible and has text, use that searched id
    student_year = getattr(window, "student_year", None)
    student_id_target = None
    if role == "student":
        student_id_target = getattr(window, "student_id", None)
    else:
        # faculty/other roles: use StudentSearch when visible and non-empty
        try:
            if hasattr(window, "StudentSearch") and window.StudentSearch.isVisible() and window.StudentSearch.text().strip():
                student_id_target = window.StudentSearch.text().strip()
        except Exception:
            student_id_target = None

    if not student_year and student_id_target:
        try:
            student_year = get_student_year(student_id_target) or "1st Year"
        except Exception:
            student_year = "1st Year"
    if not student_year:
        student_year = "1st Year"
    order = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    if student_year not in order:
        return
    max_idx = order.index(student_year)
    allowed = set(order[: max_idx + 1])
    # Collect current items
    current_items = [box.itemText(i) for i in range(box.count())]
    # If items already match restriction, skip
    if all(item in allowed for item in current_items) and all(y in current_items for y in allowed):
        return
    # Rebuild with allowed items only
    try:
        box.blockSignals(True)
        box.clear()
        for y in order[: max_idx + 1]:
            box.addItem(y)
        # Ensure selection is valid
        box.setCurrentIndex(min(box.currentIndex() if box.currentIndex() >= 0 else 0, max_idx))
    finally:
        box.blockSignals(False)
    _populate_curriculum(window)
