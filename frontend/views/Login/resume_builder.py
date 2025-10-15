from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QFrame, QListWidget, QListWidgetItem, QTextEdit, QComboBox,
    QWidget, QFileDialog, QScrollArea, QScrollBar
)


class ResumeBuilderDialog(QDialog):
    def __init__(self, parent=None, session=None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.session = session or getattr(parent, "session", {}) or {}
        self.setWindowTitle("Resume Builder")
        self.setModal(True)
        self.setFixedSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background: #BDBDBD;
                border-radius: 18px;
                border: 1px solid #d1d5db;
            }
            QLabel {
                font: 14px;
                color: #333;
                background: transparent;
            }
            QLineEdit, QComboBox, QTextEdit {
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 8px;
                background: #fdfdfe;
                min-height: 38px;
            }
            QTextEdit {
                min-height: 120px;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background: #f4f5f7; border-right: 1px solid #e0e0e0;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background: #e5e7eb;
            }
            QListWidget::item:selected {
                background: #084924;
                color: white;
                font-weight: bold;
            }
        """)
        sidebar_layout.addWidget(self.nav_list)

        nav_items = ["Personal Details", "Resume Objective", "Work Experience", "Education", "Skills", "Interests"]
        for item_text in nav_items:
            self.nav_list.addItem(QListWidgetItem(item_text))

        sidebar_layout.addStretch()

        save_close_btn = QPushButton("Save & Close")
        save_close_btn.setFixedHeight(40)
        save_close_btn.setStyleSheet("""
            QPushButton {
                background: #15803d;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #166534;
            }
        """)
        sidebar_layout.addWidget(save_close_btn)
        save_close_btn.clicked.connect(self.save_and_close)

        main_layout.addWidget(sidebar)

        # Content area
        content_area = QFrame()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)

        # Bottom navigation buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.back_btn = QPushButton("< Back")
        self.back_btn.setFixedSize(100, 40)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: #166534;
                color: white;
            }
            QPushButton:hover {
                background: #15803d;
            }
        """)
        buttons_layout.addWidget(self.back_btn)

        self.next_step_btn = QPushButton("Next step >")
        self.next_step_btn.setFixedSize(150, 40)
        self.next_step_btn.setStyleSheet("""
            QPushButton {
                background: #15803d;
                color: white;
            }
            QPushButton:hover {
                background: #166534;
            }
        """)
        buttons_layout.addWidget(self.next_step_btn)

        content_layout.addLayout(buttons_layout)


        # Create pages
        self.create_personal_details_page()
        self.create_objective_page()
        self.create_experience_page()
        self.create_education_page()
        self.create_skills_page()
        self.create_interests_page()

        main_layout.addWidget(content_area, 1)

        # Connections
        self.nav_list.currentRowChanged.connect(self.update_button_states)
        self.next_step_btn.clicked.connect(self.next_page)
        self.back_btn.clicked.connect(self.prev_page)

        self.nav_list.setCurrentRow(0)
        self.update_button_states(0)
        
        self._seed_initial_data()  
        self.nav_list.setCurrentRow(0)
        self.update_button_states(0)

    # Start of seeding process
    def _api_base(self):
        try:
            from services.auth_service import BASE_API_URL
            return BASE_API_URL.rstrip("/")
        except Exception:
            return "http://127.0.0.1:8000"

    def _auth_headers(self):
        tok = self.session.get("token")
        return {"Authorization": f"Bearer {tok}", "Accept":"application/json"} if tok else {}

    def _get(self, path):
        if not self._auth_headers(): return None
        import requests
        url = f"{self._api_base().rstrip('/')}/{path.lstrip('/')}"
        try:
            r = requests.get(url, headers=self._auth_headers(), timeout=8)
            return r.json() if r.ok else None
        except Exception:
            return None
    def _seed_initial_data(self):
        self._seed_personal()
        self._seed_education()
        self._seed_experience()
        self._seed_skills()
        self._seed_interests()
    def _seed_personal(self):
        me = self._get("api/users/me/")
        if not me: return
        self.first_name.setText(me.get("first_name") or "")
        self.last_name.setText(me.get("last_name") or "")
        self.email.setText(me.get("email") or "")
        self.phone.setText(me.get("phone_number") or "")
        # address/city/zip not in model; keep defaults
    def _seed_education(self):
        items = self._get("api/users/resume/education/") or []
        if not items: return
        edu = items[0]  # ordered by created_at desc in viewset
        self.degree.setText(edu.get("degree") or "")
        self.school.setText(edu.get("school") or "")
        self.edu_city.setText(edu.get("city") or "")
        self._set_combo(self.edu_start_month, edu.get("start_month"))
        self.edu_start_year.setText(edu.get("start_year") or "")
        self._set_combo(self.edu_end_month, edu.get("end_month"))
        self.edu_end_year.setText(edu.get("end_year") or "")
        self.edu_description_editor.setPlainText(edu.get("description") or "")
    def _seed_experience(self):
        items = self._get("api/users/resume/experience/") or []
        if not items: return
        exp = items[0]
        self.job_title.setText(exp.get("job_title") or "")
        self.employer.setText(exp.get("employer") or "")
        self.exp_city.setText(exp.get("city") or "")
        self._set_combo(self.exp_start_month, exp.get("start_month"))
        self.exp_start_year.setText(exp.get("start_year") or "")
        self._set_combo(self.exp_end_month, exp.get("end_month"))
        self.exp_end_year.setText(exp.get("end_year") or "")
        self.exp_description_editor.setPlainText(exp.get("description") or "")
    def _seed_skills(self):
        items = self._get("api/users/resume/skills/") or []
        for it in items:
            self._add_skill_label(
                it.get("name",""), it.get("level",""),
                it.get("award",""), it.get("date_received",""),
                it.get("presenter","")
        )

    def _add_skill_label(self, skill, level, award, date, presenter):
        if not (skill or award): return
        txt = f"• {skill}" + (f" ({level})" if level else "")
        if award: txt += f" - Award: {award}"
        if date:  txt += f" ({date})"
        if presenter: txt += f" by {presenter}"
        lbl = QLabel(txt)
        lbl.setStyleSheet("QLabel{padding:8px;background:#f8f9fa;border-radius:4px;margin:2px 0;}")
        self.skills_list_layout.addWidget(lbl)
    def _seed_interests(self):
        items = self._get("api/users/resume/interests/") or []
        for it in items:
            name = it.get("name")
            if not name: continue
            lbl = QLabel(f"• {name}")
            lbl.setStyleSheet("QLabel{padding:8px;background:#f8f9fa;border-radius:4px;margin:2px 0;}")
            self.hobbies_list_layout.addWidget(lbl)
    def _set_combo(self, combo: QComboBox, value: str | None):
        if not value: return
        idx = combo.findText(value, Qt.MatchFlag.MatchFixedString)
        if idx >= 0: combo.setCurrentIndex(idx)








    def add_photo(self):
        """Open a file dialog to select and set a profile photo."""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale the image to fit the placeholder while maintaining aspect ratio
                pixmap = pixmap.scaled(160, 160, 
                                     Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
                
                # Clear the existing layout
                while self.photo_placeholder.layout().count():
                    item = self.photo_placeholder.layout().takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                
                # Create a label to display the image
                photo_label = QLabel()
                photo_label.setPixmap(pixmap)
                photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                photo_label.setStyleSheet("background: transparent;")
                
                # Add the label to the photo placeholder
                self.photo_placeholder.layout().addWidget(photo_label)
                
                # Store the photo path for later use
                self.photo_path = file_path

    def create_personal_details_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)

        title = QLabel("Personal Details")
        title.setStyleSheet("font: 20px bold; color: #111;")
        layout.addWidget(title)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(30)

        # Photo upload
        photo_area = QVBoxLayout()
        self.photo_placeholder = QPushButton()
        self.photo_placeholder.setFixedSize(160, 160)
        self.photo_placeholder.setStyleSheet("""
            QPushButton {
                border: 1px dashed #ccc;
                border-radius: 10px;
                background: #f9fafb;
            }
            QPushButton:hover {
                background: #f0f2f5;
            }
        """)
        
        # Add photo layout
        photo_inner_layout = QVBoxLayout(self.photo_placeholder)
        photo_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_icon = QLabel("📷")
        camera_icon.setStyleSheet("font-size: 42px; background: transparent;")
        camera_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_photo_text = QLabel("Add photo (optional)")
        add_photo_text.setStyleSheet("color: #666; background: transparent;")
        add_photo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_inner_layout.addWidget(camera_icon)
        photo_inner_layout.addWidget(add_photo_text)
        
        # Add the photo area to the form
        photo_area.addWidget(self.photo_placeholder)
        form_layout.addLayout(photo_area)
        
        # Connect the click event
        self.photo_placeholder.clicked.connect(self.add_photo)


        # Fields
        fields_layout = QGridLayout()
        fields_layout.setSpacing(15)

        fields_layout.addWidget(QLabel("First name*"), 0, 0)
        self.first_name = QLineEdit("Mark")
        fields_layout.addWidget(self.first_name, 1, 0)

        fields_layout.addWidget(QLabel("Last name*"), 0, 1)
        self.last_name = QLineEdit("Importante")
        fields_layout.addWidget(self.last_name, 1, 1)

        fields_layout.addWidget(QLabel("Email address*"), 2, 0)
        self.email = QLineEdit("importantemark@gmail.com")
        fields_layout.addWidget(self.email, 3, 0)

        fields_layout.addWidget(QLabel("Phone number"), 2, 1)
        self.phone = QLineEdit()
        fields_layout.addWidget(self.phone, 3, 1)

        fields_layout.addWidget(QLabel("Address"), 4, 0, 1, 2)
        self.address = QLineEdit("Lapu-Lapu street")
        fields_layout.addWidget(self.address, 5, 0, 1, 2)

        fields_layout.addWidget(QLabel("Zip code"), 6, 0)
        self.zip_code = QLineEdit("8709")
        fields_layout.addWidget(self.zip_code, 7, 0)

        fields_layout.addWidget(QLabel("City/Town"), 6, 1)
        self.city = QLineEdit("VALENCIA CITY")
        fields_layout.addWidget(self.city, 7, 1)

        form_layout.addLayout(fields_layout, 1)
        layout.addLayout(form_layout)
        self.stack.addWidget(page)

    def create_objective_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("👤 Resume Objective")
        title.setStyleSheet("font: 18px bold; color: #111;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Description"))
        self.objective_editor = QTextEdit()
        layout.addWidget(self.objective_editor, 1)
        self.stack.addWidget(page)

    def create_experience_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)

        title = QLabel("💼 Work Experience")
        title.setStyleSheet("font: 20px bold; color: #111;")
        layout.addWidget(title)

        form_layout = QGridLayout()
        form_layout.setSpacing(15)

        form_layout.addWidget(QLabel("Job Title"), 0, 0)
        self.job_title = QLineEdit()
        form_layout.addWidget(self.job_title, 1, 0)

        form_layout.addWidget(QLabel("City/Town"), 0, 1)
        self.exp_city = QLineEdit()
        form_layout.addWidget(self.exp_city, 1, 1)

        form_layout.addWidget(QLabel("Employer"), 2, 0, 1, 2)
        self.employer = QLineEdit()
        form_layout.addWidget(self.employer, 3, 0, 1, 2)

        form_layout.addWidget(QLabel("Start Date"), 4, 0)
        self.exp_start_month = QComboBox()
        self.exp_start_month.addItems(
            ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"])
        self.exp_start_year = QLineEdit("2018")
        start_layout = QHBoxLayout()
        start_layout.addWidget(self.exp_start_month)
        start_layout.addWidget(self.exp_start_year)
        form_layout.addLayout(start_layout, 5, 0)

        form_layout.addWidget(QLabel("End Date"), 4, 1)
        self.exp_end_month = QComboBox()
        self.exp_end_month.addItems(
            ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"])
        self.exp_end_year = QLineEdit("2018")
        end_layout = QHBoxLayout()
        end_layout.addWidget(self.exp_end_month)
        end_layout.addWidget(self.exp_end_year)
        form_layout.addLayout(end_layout, 5, 1)

        form_layout.addWidget(QLabel("Description"), 6, 0, 1, 2)
        self.exp_description_editor = QTextEdit()
        form_layout.addWidget(self.exp_description_editor, 7, 0, 1, 2)

        form_layout.setRowStretch(7, 1)

        layout.addLayout(form_layout, 1)
        self.stack.addWidget(page)

    def create_education_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)

        title = QLabel("🎓 Education and Qualifications")
        title.setStyleSheet("font: 20px bold; color: #111;")
        layout.addWidget(title)

        form_layout = QGridLayout()
        form_layout.setSpacing(15)

        form_layout.addWidget(QLabel("Degree"), 0, 0)
        self.degree = QLineEdit()
        form_layout.addWidget(self.degree, 1, 0)

        form_layout.addWidget(QLabel("City/Town"), 0, 1)
        self.edu_city = QLineEdit()
        form_layout.addWidget(self.edu_city, 1, 1)

        form_layout.addWidget(QLabel("School"), 2, 0, 1, 2)
        self.school = QLineEdit()
        form_layout.addWidget(self.school, 3, 0, 1, 2)

        form_layout.addWidget(QLabel("Start Date"), 4, 0)
        self.edu_start_month = QComboBox()
        self.edu_start_month.addItems(
            ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"])
        self.edu_start_year = QLineEdit("2018")
        start_layout = QHBoxLayout()
        start_layout.addWidget(self.edu_start_month)
        start_layout.addWidget(self.edu_start_year)
        form_layout.addLayout(start_layout, 5, 0)

        form_layout.addWidget(QLabel("End Date"), 4, 1)
        self.edu_end_month = QComboBox()
        self.edu_end_month.addItems(
            ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"])
        self.edu_end_year = QLineEdit("2022")
        end_layout = QHBoxLayout()
        end_layout.addWidget(self.edu_end_month)
        end_layout.addWidget(self.edu_end_year)
        form_layout.addLayout(end_layout, 5, 1)

        form_layout.addWidget(QLabel("Description"), 6, 0, 1, 2)
        self.edu_description_editor = QTextEdit()
        form_layout.addWidget(self.edu_description_editor, 7, 0, 1, 2)

        form_layout.setRowStretch(7, 1)

        layout.addLayout(form_layout, 1)
        self.stack.addWidget(page)

    def create_skills_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)

        title = QLabel("🛠 Skills")
        title.setStyleSheet("font: 20px bold; color: #111;")
        layout.addWidget(title)

        # Skills form
        form_layout = QGridLayout()
        form_layout.setSpacing(15)

        # Skill input
        form_layout.addWidget(QLabel("Skill"), 0, 0)
        self.skill_input = QLineEdit()
        self.skill_input.setPlaceholderText("e.g. Microsoft Word")
        form_layout.addWidget(self.skill_input, 1, 0)

        # Level dropdown
        form_layout.addWidget(QLabel("Level"), 0, 1)
        self.skill_level = QComboBox()
        self.skill_level.addItems(["Select level", "Beginner", "Intermediate", "Advanced", "Expert"])
        form_layout.addWidget(self.skill_level, 1, 1)

        # Award name
        form_layout.addWidget(QLabel("Award Name (if any)"), 2, 0)
        self.award_name = QLineEdit()
        self.award_name.setPlaceholderText("Enter award name (if any)")
        form_layout.addWidget(self.award_name, 3, 0)

        # Date received
        form_layout.addWidget(QLabel("Date Received"), 2, 1)
        self.date_received = QLineEdit()
        self.date_received.setPlaceholderText("Enter date received")
        form_layout.addWidget(self.date_received, 3, 1)

        # Presenter
        form_layout.addWidget(QLabel("Presenter (if any)"), 4, 0, 1, 2)
        self.presenter = QLineEdit()
        self.presenter.setPlaceholderText("Enter presenter name (if any)")
        form_layout.addWidget(self.presenter, 5, 0, 1, 2)

        layout.addLayout(form_layout)

        # Add another skill link
        self.add_skill_link = QLabel("➕ Add another skill")
        self.add_skill_link.setStyleSheet("""
            QLabel {
                color: #666;
                text-decoration: underline;
            }
            QLabel:hover {
                color: #333;
            }
        """)
        self.add_skill_link.mousePressEvent = lambda event: self.add_skill_row()
        layout.addWidget(self.add_skill_link)

        # Skills list container
        self.skills_list_layout = QVBoxLayout()
        layout.addLayout(self.skills_list_layout, 1)

        # Bottom buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedSize(80, 35)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #666;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #e9e9e9;
            }
        """)
        buttons_layout.addWidget(delete_btn)

        save_btn = QPushButton("Save")
        save_btn.setFixedSize(80, 35)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #666;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #e9e9e9;
            }
        """)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)
        self.stack.addWidget(page)

    def add_skill_row(self):
        # Add current skill to the list if it has content
        if self.skill_input.text().strip():
            skill_text = self.skill_input.text().strip()
            level_text = self.skill_level.currentText()
            award_text = self.award_name.text().strip()
            date_text = self.date_received.text().strip()
            presenter_text = self.presenter.text().strip()
            
            # Create display text
            display_text = f"• {skill_text} ({level_text})"
            if award_text:
                display_text += f" - Award: {award_text}"
            if date_text:
                display_text += f" ({date_text})"
            if presenter_text:
                display_text += f" by {presenter_text}"
            
            # Create a simple label to display the skill
            skill_label = QLabel(display_text)
            skill_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    margin: 2px 0;
                }
            """)
            
            self.skills_list_layout.addWidget(skill_label)
            
            # Clear the input fields
            self.skill_input.clear()
            self.skill_level.setCurrentIndex(0)
            self.award_name.clear()
            self.date_received.clear()
            self.presenter.clear()
            
            # Set focus back to skill input
            self.skill_input.setFocus()

    def create_interests_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)

        title = QLabel("❤️ Interests")
        title.setStyleSheet("font: 20px bold; color: #111;")
        layout.addWidget(title)

        # Hobby input
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        form_layout.addWidget(QLabel("Hobby"))
        self.hobby_input = QLineEdit()
        self.hobby_input.setPlaceholderText("e.g. Hiking")
        form_layout.addWidget(self.hobby_input)

        layout.addLayout(form_layout)

        # Add another hobby link
        self.add_hobby_link = QLabel("➕ Add another hobby")
        self.add_hobby_link.setStyleSheet("""
            QLabel {
                color: #666;
                text-decoration: underline;
            }
            QLabel:hover {
                color: #333;
            }
        """)
        self.add_hobby_link.mousePressEvent = lambda event: self.add_hobby_row()
        layout.addWidget(self.add_hobby_link)

        # Hobbies list container
        self.hobbies_list_layout = QVBoxLayout()
        layout.addLayout(self.hobbies_list_layout, 1)

        # Bottom buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedSize(80, 35)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #666;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #e9e9e9;
            }
        """)
        buttons_layout.addWidget(delete_btn)

        save_btn = QPushButton("Save")
        save_btn.setFixedSize(80, 35)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #666;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #e9e9e9;
            }
        """)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)
        self.stack.addWidget(page)


    def add_hobby_row(self):
        # Add current hobby to the list if it has content
        if self.hobby_input.text().strip():
            hobby_text = self.hobby_input.text().strip()
            
            # Create a simple label to display the hobby
            hobby_label = QLabel(f"• {hobby_text}")
            hobby_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    margin: 2px 0;
                }
            """)
            
            self.hobbies_list_layout.addWidget(hobby_label)
            
            # Clear the input field
            self.hobby_input.clear()
            
            # Set focus back to hobby input
            self.hobby_input.setFocus()


    # --- Navigation ---
    def update_button_states(self, index):
        self.stack.setCurrentIndex(index)
        self.back_btn.setEnabled(index > 0)
        if index == self.stack.count() - 1:
            self.next_step_btn.setEnabled(False)
        else:
            self.next_step_btn.setEnabled(True)

    def next_page(self):
        row = self.nav_list.currentRow()
        if row < self.nav_list.count() - 1:
            self.nav_list.setCurrentRow(row + 1)

    def prev_page(self):
        row = self.nav_list.currentRow()
        if row > 0:
            self.nav_list.setCurrentRow(row - 1)

    def save_and_close(self):
        # Collect skills from the skills list layout
        skills = []
        for i in range(self.skills_list_layout.count()):
            skill_label = self.skills_list_layout.itemAt(i).widget()
            if skill_label and isinstance(skill_label, QLabel):
                skill_text = skill_label.text()
                # Extract skill and level from the label text "• Skill Name (Level) - Award: AwardName (Date) by Presenter"
                if skill_text.startswith("• "):
                    # Remove the bullet point
                    skill_text = skill_text[2:]
                    
                    # Parse the skill and level
                    if " (" in skill_text:
                        skill_part = skill_text[:skill_text.find(" (")]
                        remaining = skill_text[skill_text.find(" (") + 2:]
                        
                        if ")" in remaining:
                            level_part = remaining[:remaining.find(")")]
                            remaining = remaining[remaining.find(")") + 1:].strip()
                            
                            skill_data = {
                                'skill': skill_part,
                                'level': level_part
                            }
                            
                            # Parse award information if present
                            if " - Award: " in remaining:
                                award_part = remaining[remaining.find(" - Award: ") + 10:]
                                if " (" in award_part:
                                    award_name = award_part[:award_part.find(" (")]
                                    date_part = award_part[award_part.find(" (") + 2:award_part.find(")")]
                                    skill_data['award'] = award_name
                                    skill_data['date'] = date_part
                                    
                                    # Check for presenter
                                    if " by " in award_part:
                                        presenter_part = award_part[award_part.find(" by ") + 4:]
                                        skill_data['presenter'] = presenter_part
                                else:
                                    skill_data['award'] = award_part
                            elif remaining:
                                # Just award name without date
                                skill_data['award'] = remaining
                            
                            skills.append(skill_data)
        
        # Collect hobbies from the hobbies list layout
        hobbies = []
        for i in range(self.hobbies_list_layout.count()):
            hobby_label = self.hobbies_list_layout.itemAt(i).widget()
            if hobby_label and isinstance(hobby_label, QLabel):
                hobby_text = hobby_label.text()
                # Extract hobby from the label text "• Hobby Name"
                if hobby_text.startswith("• "):
                    hobby = hobby_text[2:]
                    hobbies.append(hobby)

        resume_data = {
            'personal_details': {
                'first_name': self.first_name.text(),
                'last_name': self.last_name.text(),
                'email': self.email.text(),
                'phone': self.phone.text(),
                'address': self.address.text(),
                'city': self.city.text(),
                'zip_code': self.zip_code.text()
            },
            'objective': self.objective_editor.toPlainText(),
            'experience': [{
                'job_title': self.job_title.text(),
                'employer': self.employer.text(),
                'city': self.exp_city.text(),
                'start_date': f"{self.exp_start_month.currentText()} {self.exp_start_year.text()}",
                'end_date': f"{self.exp_end_month.currentText()} {self.exp_end_year.text()}",
                'description': self.exp_description_editor.toPlainText()
            }],
            'education': [{
                'degree': self.degree.text(),
                'school': self.school.text(),
                'city': self.edu_city.text(),
                'start_date': f"{self.edu_start_month.currentText()} {self.edu_start_year.text()}",
                'end_date': f"{self.edu_end_month.currentText()} {self.edu_end_year.text()}",
                'description': self.edu_description_editor.toPlainText()
            }],
            'skills': skills,
            'interests': hobbies
        }

        # Print the collected data (you can save to file or database here)
        import json
        print("\n--- Resume Data ---")
        print(json.dumps(resume_data, indent=2))
        print("-------------------\n")

        self.accept()