from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QStackedWidget, QGraphicsDropShadowEffect,
    QDialog, QListWidget, QListWidgetItem, QGraphicsBlurEffect,
    QLineEdit, QGridLayout
)
try:
    from .resume_builder import ResumeBuilderDialog
except Exception:
    try:
        from views.Login.resume_builder import ResumeBuilderDialog
    except Exception:
        from frontend.views.Login.resume_builder import ResumeBuilderDialog  # fallback


class ChangeProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Change Profile Picture")
        self.setModal(True)
        self.setFixedSize(520, 400)
        self.setStyleSheet("""
            QDialog { 
                background: white; 
                border-radius: 18px;
                border: 1px solid #d1d5db;
            }
            QPushButton { 
                border: none; 
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # Title
        title = QLabel("Change Profile Picture")
        title.setStyleSheet("font: 22px bold; color: #14532d; margin-bottom: 20px; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Main content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)

        # Left side - Recent Uploaded Images
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)
        
        recent_label = QLabel("Recent Uploaded Images")
        recent_label.setStyleSheet("font: 15px bold; color: #084924; margin-bottom: 8px; background: transparent;")
        left_layout.addWidget(recent_label)
        
        # Recent images list
        self.recent_list = QListWidget()
        self.recent_list.setFixedSize(180, 180)
        self.recent_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d1d5db;
                border-radius: 10px;
                background: #f9fafb;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e5e7eb;
                background: transparent;
            }
            QListWidget::item:selected {
                background: transparent;
                color: inherit;
            }
            QListWidget::item:hover {
                background: #f0f0f0;
            }
        """)
        
        # Add sample recent images
        for i in range(3):
            item = QListWidgetItem(f"Profile_{i+1}.png")
            self.recent_list.addItem(item)
            
        left_layout.addWidget(self.recent_list)
        content_layout.addLayout(left_layout)

        # Right side - Upload File
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)
        
        upload_label = QLabel("Upload File")
        upload_label.setStyleSheet("font: 15px bold; color: #14532d; margin-bottom: 8px; background: transparent;")
        right_layout.addWidget(upload_label)
        
        # Upload area
        upload_frame = QFrame()
        upload_frame.setFixedSize(180, 180)
        upload_frame.setStyleSheet("""
            QFrame {
                border: 2px dashed #9ca3af;
                border-radius: 10px;
                background: #f9fafb;
            }
        """)
        
        upload_inner = QVBoxLayout(upload_frame)
        upload_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_inner.setSpacing(12)
        
        
        # Upload text
        upload_text = QLabel("Drag & Drop here\nor")
        upload_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_text.setStyleSheet("color: #6b7280; background: transparent;")
        upload_inner.addWidget(upload_text)
        
        # Browse button
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedSize(100, 32)
        browse_btn.setStyleSheet("""
            QPushButton {
                background: #084924;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #06381c;
            }
        """)
        browse_btn.clicked.connect(self.browse_image)
        upload_inner.addWidget(browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        right_layout.addWidget(upload_frame)
        content_layout.addLayout(right_layout)

        layout.addLayout(content_layout)

        # Buttons at the bottom
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setFixedSize(100, 36)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #084924;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #06381c;
            }
        """)
        save_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)

        self.selected_image = None

    def browse_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.selected_image = file
            item = QListWidgetItem(file.split("/")[-1])
            self.recent_list.insertItem(0, item)
            QMessageBox.information(self, "Selected", f"Selected file:\n{file}")


class AddEducationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Add Education")
        self.setModal(True)
        self.setFixedSize(440, 260)
        self.setStyleSheet("""
            QDialog { background: white; border-radius: 18px; border: 1px solid #d1d5db; }
            QLabel { font: 14px; color: #333; background: transparent; }
            QLineEdit { border: 1px solid #ccc; border-radius: 10px; padding: 8px; }
            QPushButton { 
                background: #198754; 
                color: white; 
                border: none; 
                border-radius: 10px; 
                padding: 8px 16px; 
                font-weight: bold; 
            }
            QPushButton:hover {
                background: #166534;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Degree
        self.degree = QLineEdit()
        self.degree.setPlaceholderText("Enter your degree")
        layout.addWidget(self.degree)

        # Institution
        self.institution = QLineEdit()
        self.institution.setPlaceholderText("Enter institution name")
        layout.addWidget(self.institution)

        # Duration
        self.duration = QLineEdit()
        self.duration.setPlaceholderText("Enter duration (e.g., 2018-2022)")
        layout.addWidget(self.duration)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        save = QPushButton("Save")
        save.clicked.connect(self.accept)
        btns.addWidget(save)

        layout.addLayout(btns)


class AddWorkExperienceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Add Work Experience")
        self.setModal(True)
        self.setFixedSize(440, 260)
        self.setStyleSheet("""
            QDialog { background: white; border-radius: 18px; border: 1px solid #d1d5db; }
            QLabel { font: 14px; color: #333; background: transparent; }
            QLineEdit { border: 1px solid #ccc; border-radius: 10px; padding: 8px; }
            QPushButton { 
                background: #198754; 
                color: white; 
                border: none; 
                border-radius: 10px; 
                padding: 8px 16px; 
                font-weight: bold; 
            }
            QPushButton:hover {
                background: #166534;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Company
        self.company = QLineEdit()
        self.company.setPlaceholderText("Enter company name")
        layout.addWidget(self.company)

        # Position
        self.position = QLineEdit()
        self.position.setPlaceholderText("Enter your position")
        layout.addWidget(self.position)

        # Duration
        self.duration = QLineEdit()
        self.duration.setPlaceholderText("Enter duration (e.g., 2020-2022)")
        layout.addWidget(self.duration)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        save = QPushButton("Save")
        save.clicked.connect(self.accept)
        btns.addWidget(save)

        layout.addLayout(btns)


class AddSkillAwardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Add Skill/Award")
        self.setModal(True)
        self.setFixedSize(480, 420)  # ⬅ Bigger height for 5 fields
        self.setStyleSheet("""
            QDialog { 
                background: white; 
                border-radius: 18px; 
                border: 1px solid #d1d5db; 
            }
            QLabel { font: 14px; color: #333; background: transparent; }
            QLineEdit { 
                border: 1px solid #ccc; 
                border-radius: 10px; 
                padding: 10px; 
                font-size: 14px;
            }
            QPushButton { 
                background: #198754; 
                color: white; 
                border: none; 
                border-radius: 10px; 
                padding: 10px 18px; 
                font-weight: bold; 
            }
            QPushButton:hover {
                background: #166534;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Skill
        self.skill = QLineEdit()
        self.skill.setPlaceholderText("Enter skill name")
        layout.addWidget(self.skill)

        # Proficiency
        self.proficiency = QLineEdit()
        self.proficiency.setPlaceholderText("Enter proficiency level")
        layout.addWidget(self.proficiency)

        # Award
        self.award = QLineEdit()
        self.award.setPlaceholderText("Enter award name (if any)")
        layout.addWidget(self.award)

        # Date
        self.date = QLineEdit()
        self.date.setPlaceholderText("Enter date received")
        layout.addWidget(self.date)

        # Presenter
        self.presenter = QLineEdit()
        self.presenter.setPlaceholderText("Enter presenter name (if any)")
        layout.addWidget(self.presenter)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        save = QPushButton("Save")
        save.clicked.connect(self.accept)
        btns.addWidget(save)

        layout.addLayout(btns)

# API base autodetect
API_BASE = "http://127.0.0.1:8000"
try:
    from services.auth_service import BASE_API_URL as _BASE
    if _BASE:
        API_BASE = _BASE
except Exception:
    pass


class ProfileWidget(QWidget):
    def __init__(self, session: dict | None = None, user: dict | None = None):
        super().__init__()
        self.session = session or {}
        self.user = user or {}

        self.setStyleSheet("background:#f4f5f7;")
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # ---------------- Profile Title ----------------
        title = QLabel("Profile")
        title.setStyleSheet("font:22px bold;color:#14532d;margin:12px 0 8px;background:transparent;")
        root.addWidget(title)

        # ---------------- Main Content ----------------
        main = QHBoxLayout()
        main.setSpacing(24)

        # ---- Profile Card (left) ----
        profile_card = QFrame()
        profile_card.setStyleSheet("background:white;border-radius:12px;")
        profile_card.setFixedSize(360, 520)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        profile_card.setGraphicsEffect(shadow)

        p = QVBoxLayout(profile_card)
        p.setContentsMargins(30, 30, 30, 30)
        p.setSpacing(16)

        self.avatar_lbl = QLabel()
        self.avatar_lbl.setFixedSize(140, 140)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet("border:3px solid #dee2e6;border-radius:70px;background:#e9ecef;")
        p.addWidget(self.avatar_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        # big labels under avatar
        self.inst_id_big = QLabel("—")
        self.inst_id_big.setStyleSheet("font:18px bold;color:#1e4d2b;background:transparent;")
        p.addWidget(self.inst_id_big, alignment=Qt.AlignmentFlag.AlignCenter)

        self.email_big = QLabel("—")
        self.email_big.setStyleSheet("color:#6c757d;background:transparent;")
        p.addWidget(self.email_big, alignment=Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("Change Profile Picture")
        btn.setFixedSize(200, 36)
        btn.setStyleSheet("background:#084924;color:white;border:none;border-radius:8px;font-weight:bold")
        btn.clicked.connect(self.show_change_page)
        p.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Info rows (dynamic)
        self.rows = {}
        for k, key in [
            ("Name", "full_name"),
            ("Course", "program"),
            ("Role", "primary_role"),
            ("Year", "year_level"),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{k}:", styleSheet="font-weight:bold;background:transparent;"))
            lbl = QLabel("—"); lbl.setStyleSheet("background:transparent;")
            row.addWidget(lbl)
            p.addLayout(row)
            self.rows[key] = lbl

        p.addStretch()

        # ---- Resume Card (right) ----
        resume_card = QFrame()
        resume_card.setStyleSheet("background:white; border-radius:12px;")
        resume_card.setFixedSize(640, 520)

        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(12); shadow2.setOffset(0, 2)
        resume_card.setGraphicsEffect(shadow2)

        r = QVBoxLayout(resume_card)
        r.setContentsMargins(20, 20, 20, 20)
        r.setSpacing(8)

        resume_title = QLabel("Resume")
        resume_title.setStyleSheet("font:18px bold; color:#084924;background:transparent;")
        r.addWidget(resume_title)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFixedHeight(1)
        line.setStyleSheet("background:#d3d3d3; margin:4px 0;")
        r.addWidget(line)

        section_header = QHBoxLayout()
        self.section_title = QLabel("Education")
        self.section_title.setStyleSheet("font-size:14px;font-weight:bold;color:#084924;background:transparent;")
        section_header.addWidget(self.section_title); section_header.addStretch()

        add_btn = QPushButton("+"); add_btn.setFixedSize(24, 24)
        add_btn.setStyleSheet("""
            QPushButton { background:#15803d;color:white;border-radius:12px;font-weight:bold; }
            QPushButton:hover { background:#166534; }
        """)
        add_btn.clicked.connect(lambda: self.handle_add_click())
        section_header.addWidget(add_btn)
        r.addLayout(section_header)

        self.resume_stack = QStackedWidget()

        # 1) Education
        edu_widget = QWidget(); edu_layout = QVBoxLayout(edu_widget)
        self.table1 = QTableWidget(0, 2)
        self.table1.setHorizontalHeaderLabels(["School", "School Year"])
        edu_layout.addWidget(self.table1)
        self.resume_stack.addWidget(edu_widget)

        # 2) Work
        work_widget = QWidget(); work_layout = QVBoxLayout(work_widget)
        self.table2 = QTableWidget(0, 2)
        self.table2.setHorizontalHeaderLabels(["Company", "Duration"])
        work_layout.addWidget(self.table2)
        self.resume_stack.addWidget(work_widget)

        # 3) Skills & Awards
        skills_widget = QWidget(); skills_layout = QVBoxLayout(skills_widget)
        self.table3 = QTableWidget(0, 5)
        self.table3.setHorizontalHeaderLabels(["Skill", "Proficiency", "Award", "Date", "Presenter"])
        self.table3.verticalHeader().setDefaultSectionSize(60)
        skills_layout.addWidget(self.table3)
        self.resume_stack.addWidget(skills_widget)

        # style
        self.make_table(self.table1, "#14532d")
        self.make_table(self.table2, "#084924")
        self.make_table(self.table3, "#084924")

        r.addWidget(self.resume_stack)
        
        self.load_resume()


        # pagination
        self.page_buttons = []
        pagination = QHBoxLayout(); pagination.addStretch()
        for i in range(1, 4):
            b = QPushButton(str(i)); b.setFixedSize(32, 32)
            b.setStyleSheet("background:#084924;color:white;border-radius:6px;" if i == 1 else
                            "background:white;color:#084924;border:1px solid #ccc;border-radius:6px;")
            b.clicked.connect(lambda _, x=i-1: self.switch_resume_section(x))
            self.page_buttons.append(b); pagination.addWidget(b)
        pagination.addStretch(); r.addLayout(pagination)

        # create resume
        cr = QHBoxLayout(); cr.addStretch()
        create_btn = QPushButton("Create Resume"); create_btn.setFixedSize(150, 36)
        create_btn.setStyleSheet("""
            QPushButton { background:#084924;color:white;border:none;border-radius:8px;font-weight:bold; }
            QPushButton:hover { background:#06381c; }
        """)
        create_btn.clicked.connect(self.show_resume_builder); cr.addWidget(create_btn); r.addLayout(cr)

        # ---- Stack (main + change picture dialog page) ----
        self.stack = QStackedWidget()
        main_page = QWidget(); ml = QHBoxLayout(main_page); ml.setSpacing(24)
        ml.addWidget(profile_card); ml.addWidget(resume_card)
        self.stack.addWidget(main_page)
        self.stack.addWidget(QWidget())  # placeholder for change page if needed
        root.addWidget(self.stack)

        # Defaults then populate
        self.set_avatar(":default")
        seed_sources = [
            self.session.get("avatar_url"),
            (self.session.get("user") or {}).get("profile_picture"),
            self.user.get("profile_picture"),
        ]
        for src in seed_sources:
            url = self._normalize_media_url(src)
            if url and self._set_avatar_from_url(url):
                break
        self._populate_from_session_then_me()


    def _normalize_media_url(self, url: str | None) -> str | None:
        if not url:
            return None
        if url.startswith(("http://", "https://")):
            return url
        base = API_BASE.rstrip("/")
        # already has MEDIA_URL prefix
        if url.startswith("/uploads/"):
            return f"{base}{url}"
        # DB-style relative path like "profile_pics/123.jpg"
        return f"{base}/uploads/{url.lstrip('/')}"

    # ---------------- Dynamic population ----------------
    def _populate_from_session_then_me(self):
        # session priming
        uname = self.session.get("username") or self.user.get("username") or "User"
        role  = (self.session.get("primary_role") or self.user.get("primary_role") or "—").title()
        email = self.user.get("email") or "—"
        inst  = self.user.get("institutional_id") or "—"

        self.rows["full_name"].setText(uname)
        self.rows["primary_role"].setText(role)
        self.email_big.setText(email)
        self.inst_id_big.setText(inst)

        # fetch /me
        token = self.session.get("token")
        if not token:
            return
        try:
            import requests
            url = f"{API_BASE.rstrip('/')}/api/users/me/"
            r = requests.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=8)
            if r.status_code != 200:
                return
            me = r.json() or {}

            # basics
            full = me.get("full_name") or " ".join(filter(None, [me.get("first_name"), me.get("last_name")])) or uname
            self.rows["full_name"].setText(full)
            self.rows["primary_role"].setText((me.get("primary_role") or role).title())
            self.email_big.setText(me.get("email") or email)
            self.inst_id_big.setText(me.get("institutional_id") or inst)

            # student data
            sp = me.get("student_profile") or {}
            prog = get_name(sp.get("program"))
            yr = sp.get("year_level")
            self.rows["program"].setText(prog or "—")
            self.rows["year_level"].setText(year_label(yr) if yr else "—")

            # avatar
            avatar = me.get("profile_picture")
            norm = self._normalize_media_url(avatar)
            if norm:
                self._set_avatar_from_url(norm)
        except Exception:
            pass

    # ---------------- Helpers ----------------
    def make_table(self, table, header_color="#15803d"):
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setWordWrap(True)
        table.setStyleSheet(f"""
            QHeaderView::section {{
                background:{header_color};color:white;font-weight:bold;height:32px;
            }}
            QTableWidget {{
                border:1px solid #e0e0e0;border-radius:8px;padding:4px;background:white;
            }}
            QTableWidget::item {{ padding:8px;border-bottom:1px solid #f0f0f0; }}
            QTableWidget::item:alternate {{ background:#f9f9f9; }}
        """)
        if table is getattr(self, "table3", None):
            table.setColumnWidth(0, 120); table.setColumnWidth(1, 100)
            table.setColumnWidth(2, 120); table.setColumnWidth(3, 80); table.setColumnWidth(4, 120)
            table.setMinimumWidth(540)
        else:
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def show_change_page(self):
        blur = QGraphicsBlurEffect(); blur.setBlurRadius(8); self.setGraphicsEffect(blur)
        dlg = ChangeProfileDialog(self)
        try:
            if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_image:
                # push to server
                self._avatar_path = dlg.selected_image
                self.save_avatar()  # uses POST /api/users/avatar/
        finally:
            self.setGraphicsEffect(None)

    def set_avatar(self, path):
        if path == ":default":
            self.avatar_lbl.setPixmap(QPixmap()); self.avatar_lbl.setText("👨‍💼")
            return
        pixmap = QPixmap(path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                      Qt.TransformationMode.SmoothTransformation)
        rounded = QPixmap(120, 120); rounded.fill(Qt.GlobalColor.transparent)
        p = QPainter(rounded); clip = QPainterPath(); clip.addEllipse(0, 0, 120, 120)
        p.setClipPath(clip); p.drawPixmap(0, 0, pixmap); p.end()
        self.avatar_lbl.setPixmap(rounded); self.avatar_lbl.setText("")

    def choose_avatar(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Picture", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self._avatar_path = file
            self.set_avatar(file)

    def save_avatar(self):
        import requests, os, mimetypes
        tok = (getattr(self, "session", {}) or {}).get("token")
        path = getattr(self, "_avatar_path", None)
        if not tok or not path:
            QMessageBox.warning(self, "Error", "Missing token or file"); return

        url = f"{API_BASE.rstrip('/')}/api/users/avatar/"

        mime = mimetypes.guess_type(path)[0] or "image/jpeg"
        with open(path, "rb") as fh:
            files = {"file": (os.path.basename(path), fh, mime)}
            headers = {"Authorization": f"Bearer {tok}", "Accept": "application/json"}
            r = requests.post(url, files=files, headers=headers, timeout=20)

        if r.ok:
            new_url = r.json().get("avatar_url", "")
            self.session["avatar_url"] = new_url
            self._set_avatar_from_url(new_url)
            QMessageBox.information(self, "Success", "Profile picture updated")
        else:
            QMessageBox.warning(self, "Upload failed", f"{r.status_code}: {r.text[:300]}")



    def show_success_message(self, message: str):
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(5)
        self.setGraphicsEffect(blur)

        box = QMessageBox(self)
        box.setWindowTitle("Success")
        box.setText(message)
        box.setIcon(QMessageBox.Icon.Information)
        box.setStyleSheet("""
            QMessageBox { background:white; border-radius:12px; padding:20px; }
            QLabel { font-size:14px; color:#14532d; background:transparent; }
            QPushButton { background:#15803d; color:white; border:none; border-radius:6px; padding:8px 16px; font-weight:bold; }
            QPushButton:hover { background:#166534; }
        """)
        box.finished.connect(lambda _: self.setGraphicsEffect(None))
        box.exec()


    def handle_add_click(self):
        idx = self.resume_stack.currentIndex()
        if idx == 0: self.add_education()
        elif idx == 1: self.add_work_experience()
        elif idx == 2: self.add_skill_award()


    def _api_base(self):
        try:
            from services.auth_service import BASE_API_URL
            return BASE_API_URL.rstrip("/")
        except Exception:
            return "http://127.0.0.1:8000"

    def _auth_headers(self):
        tok = self.session.get("token")
        return {"Authorization": f"Bearer {tok}", "Accept":"application/json"} if tok else {}

    def _resume_post(self, endpoint: str, payload: dict):
        if not self._auth_headers():
            print("Resume save skipped: no token"); return
        try:
            import requests, json
            url = f"{self._api_base()}/api/users/{endpoint.strip('/')}/"
            r = requests.post(url, json=payload, headers=self._auth_headers(), timeout=10)
            if not r.ok:
                print(f"POST {url} -> {r.status_code}: {r.text[:300]}")
        except Exception as e:
            print("Resume save error:", e)
    
    def _resume_list(self, endpoint: str):
        if not self._auth_headers():
            print("Resume load skipped: no token")
            return []
        try:
            import requests
            url = f"{self._api_base()}/api/users/{endpoint.strip('/')}/"
            r = requests.get(url, headers=self._auth_headers(), timeout=10)
            if r.ok:
                return r.json() or []
            print(f"GET {url} -> {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print("Resume list error:", e)
        return []

    def _split_years(self, duration: str):
        """Parse '2018-2022' or '2018–2022' -> ('2018','2022')."""
        if not duration: return ("","")
        for sep in ("–", "-", "—"):
            if sep in duration:
                a,b = [s.strip() for s in duration.split(sep,1)]
                return (a,b)
        return (duration.strip(),"")
    
    # Load resume contents 
    def load_resume(self):
        self._load_education()
        self._load_experience()
        self._load_skills()

    def _load_education(self):
        items = self._resume_list("resume/education")
        self.table1.setRowCount(0)
        for it in items:
            school = it.get("school","")
            degree = it.get("degree","")
            sy     = it.get("start_year","") or ""
            ey     = it.get("end_year","") or ""
            title = f"{school} — {degree}" if degree else school
            dur   = f"{sy}–{ey}" if (sy or ey) else ""
            r = self.table1.rowCount()
            self.table1.insertRow(r)
            self.table1.setItem(r, 0, QTableWidgetItem(title))
            self.table1.setItem(r, 1, QTableWidgetItem(dur))

    def _load_experience(self):
        items = self._resume_list("resume/experience")
        self.table2.setRowCount(0)
        for it in items:
            company  = it.get("employer","")
            position = it.get("job_title","")
            sy, ey   = it.get("start_year",""), it.get("end_year","")
            title = f"{company} — {position}" if position else company
            dur   = f"{sy}-{ey}" if (sy or ey) else ""
            r = self.table2.rowCount()
            self.table2.insertRow(r)
            self.table2.setItem(r, 0, QTableWidgetItem(title))
            self.table2.setItem(r, 1, QTableWidgetItem(dur))

    def _load_skills(self):
        items = self._resume_list("resume/skills")
        self.table3.setRowCount(0)
        for it in items:
            r = self.table3.rowCount()
            self.table3.insertRow(r)
            self.table3.setItem(r, 0, QTableWidgetItem(it.get("name","")))
            self.table3.setItem(r, 1, QTableWidgetItem(it.get("level","")))
            self.table3.setItem(r, 2, QTableWidgetItem(it.get("award","")))
            self.table3.setItem(r, 3, QTableWidgetItem(it.get("date_received","")))
            self.table3.setItem(r, 4, QTableWidgetItem(it.get("presenter","")))



    def add_education(self):
        blur = QGraphicsBlurEffect(); blur.setBlurRadius(5); self.setGraphicsEffect(blur)
        dlg = AddEducationDialog(self)
        dlg.finished.connect(lambda: self.setGraphicsEffect(None))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            degree   = dlg.degree.text().strip()
            school   = dlg.institution.text().strip()
            duration = dlg.duration.text().strip()
            if school and duration:
                row = self.table1.rowCount()
                self.table1.insertRow(row)
                title = f"{school}" if not degree else f"{school} — {degree}"
                self.table1.setItem(row, 0, QTableWidgetItem(title))
                self.table1.setItem(row, 1, QTableWidgetItem(duration))
                # save
                sy, ey = self._split_years(duration)
                self._resume_post("resume/education", {
                    "degree": degree, "school": school, "city": "",
                    "start_month":"", "start_year": sy, "end_month":"", "end_year": ey,
                    "description":""
                })
                self.show_success_message("Education added successfully!")
                
        self.load_resume()


    def add_work_experience(self):
        blur = QGraphicsBlurEffect(); blur.setBlurRadius(5); self.setGraphicsEffect(blur)
        dlg = AddWorkExperienceDialog(self)
        dlg.finished.connect(lambda: self.setGraphicsEffect(None))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            company  = dlg.company.text().strip()
            position = dlg.position.text().strip()
            duration = dlg.duration.text().strip()
            if company and duration:
                row = self.table2.rowCount()
                self.table2.insertRow(row)
                title = f"{company}" if not position else f"{company} — {position}"
                self.table2.setItem(row, 0, QTableWidgetItem(title))
                self.table2.setItem(row, 1, QTableWidgetItem(duration))
                # save
                sy, ey = self._split_years(duration)
                self._resume_post("resume/experience", {
                    "job_title": position or "", "employer": company, "city":"",
                    "start_month":"", "start_year": sy, "end_month":"", "end_year": ey,
                    "description":""
                })
                self.show_success_message("Work experience added successfully!")
        self.load_resume()


    def add_skill_award(self):
        blur = QGraphicsBlurEffect(); blur.setBlurRadius(5); self.setGraphicsEffect(blur)
        dlg = AddSkillAwardDialog(self)
        dlg.finished.connect(lambda: self.setGraphicsEffect(None))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            skill = dlg.skill.text().strip()
            level = dlg.proficiency.text().strip()
            award = dlg.award.text().strip()
            date  = dlg.date.text().strip()
            presenter = dlg.presenter.text().strip()
            if skill or award:
                row = self.table3.rowCount()
                self.table3.insertRow(row)
                self.table3.setItem(row, 0, QTableWidgetItem(skill))
                self.table3.setItem(row, 1, QTableWidgetItem(level))
                self.table3.setItem(row, 2, QTableWidgetItem(award))
                self.table3.setItem(row, 3, QTableWidgetItem(date))
                self.table3.setItem(row, 4, QTableWidgetItem(presenter))
                # save
                self._resume_post("resume/skills", {
                    "name": skill, "level": level, "award": award,
                    "date_received": date, "presenter": presenter
                })
                msg = "Skill and Award added successfully!" if skill and award else ("Skill added successfully!" if skill else "Award added successfully!")
                self.show_success_message(msg)
        self.load_resume()



    def _set_avatar_from_url(self, url: str, bust_cache: bool = True) -> bool:
        from urllib.parse import urljoin
        import time, requests

        base = self._api_base().rstrip("/")
        full = url if url.startswith(("http://", "https://")) else urljoin(f"{base}/", url.lstrip("/"))
        if bust_cache:
            sep = "&" if "?" in full else "?"
            full = f"{full}{sep}v={int(time.time())}"
        print("AVATAR GET ->", full)

        headers = self._auth_headers() if full.startswith(base) else {}
        try:
            r = requests.get(full, headers=headers, timeout=8)
            print("AVATAR STATUS ->", r.status_code)
            r.raise_for_status()
            pix = QPixmap()
            if not pix.loadFromData(r.content):
                raise RuntimeError("decode failed")
            pix = pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation)
            rounded = QPixmap(120, 120)
            rounded.fill(Qt.GlobalColor.transparent)
            p = QPainter(rounded)
            clip = QPainterPath(); clip.addEllipse(0, 0, 120, 120)
            p.setClipPath(clip); p.drawPixmap(0, 0, pix); p.end()
            self.avatar_lbl.setPixmap(rounded); self.avatar_lbl.setText("")
            return True
        except Exception as e:
            print("avatar fetch failed:", e)
            self.set_avatar(":default")
            return False


    def show_resume_builder(self):
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur = QGraphicsBlurEffect(); blur.setBlurRadius(5); self.setGraphicsEffect(blur)
        try:
            dlg = ResumeBuilderDialog(self, session=self.session)
            dlg.exec()
        finally:
            self.setGraphicsEffect(None)

    def switch_resume_section(self, index: int):
        titles = ["Education", "Work Experience", "Skills & Awards"]
        # guard
        if not hasattr(self, "resume_stack") or not hasattr(self, "page_buttons"):
            return
        index = max(0, min(index, self.resume_stack.count() - 1))
        self.resume_stack.setCurrentIndex(index)
        if hasattr(self, "section_title"):
            self.section_title.setText(titles[index])

        # update button styles
        for i, btn in enumerate(self.page_buttons):
            if i == index:
                btn.setStyleSheet("background:#084924;color:white;border-radius:6px;")
            else:
                btn.setStyleSheet(
                    "background:white;color:#084924;border:1px solid #ccc;border-radius:6px;"
                )


def get_name(obj):
    if not obj: return None
    if isinstance(obj, str): return obj
    for key in ("program_name","section_name","department_name","position_name","name","title"):
        if obj.get(key): return obj[key]
    return None

def year_label(n):
    try:
        n = int(n)
    except Exception:
        return str(n) if n else "—"
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")

