import sys
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QPalette, QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QLineEdit,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect
)

START_WIDTH = 1200
START_HEIGHT = 1080
MIN_WIDTH = 800
MIN_HEIGHT = 800


class ResetPasswordWidget(QWidget):
    back_to_signin_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # Prevent widget from being garbage collected
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, False)

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#f8f9fa"))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

        # Main layout split (left/right)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(40)

        # --- Left column ---
        left_layout = QVBoxLayout()
        left_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.left_logo = QLabel()
        self.left_logo.setPixmap(QPixmap("venv/images/cisc.png").scaled(220, 220,Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.left_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.left_logo)

        self.left_label = QLabel("CISC VIRTUAL HUB")
        self.left_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        self.left_label.setStyleSheet("color: #6c757d;")
        self.left_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.left_label)

        left_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addLayout(left_layout, stretch=1)

        # --- Right column ---
        right_layout = QVBoxLayout()
        right_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Card frame
        card = QFrame()
        card.setFixedWidth(500)  # Set a fixed width for the card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)
        card.setStyleSheet("QFrame { background: white; border-radius: 8px; border: none; }")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(16)

        # --- Top header with logo + university text ---
        header_layout = QHBoxLayout()
        self.uni_logo = QLabel()
        self.uni_logo.setPixmap(QPixmap("venv/images/cmu.png").scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.uni_logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.uni_logo)

        text_layout = QVBoxLayout()
        self.uni_title = QLabel("Central Mindanao University")
        self.uni_title.setStyleSheet("color: #212529;")
        self.uni_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        self.uni_subtitle = QLabel("College of Information Sciences & Computing")
        self.uni_subtitle.setStyleSheet("color: #495057;")
        self.uni_subtitle.setFont(QFont("Segoe UI", 12))

        text_layout.addWidget(self.uni_title)
        text_layout.addWidget(self.uni_subtitle)
        header_layout.addLayout(text_layout)
        card_layout.addLayout(header_layout)

        # --- Divider ---
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("color: #006400;")
        card_layout.addWidget(divider)

        # --- Form Container ---
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(16)
        card_layout.addWidget(self.form_container)

        # Back to Sign In (now part of the main card layout)
        self.back_to_signin_link = QLabel("Back to Sign in")
        self.back_to_signin_link.setStyleSheet(
            "QLabel { color: #007bff; } QLabel:hover { text-decoration: underline; }"
        )
        self.back_to_signin_link.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.back_to_signin_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_to_signin_link.mousePressEvent = self.request_back_to_signin
        card_layout.addWidget(self.back_to_signin_link)

        self.show_email_otp_ui() # Show initial UI

        # Add card to right column
        right_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        right_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addLayout(right_layout, stretch=3)

        self.setLayout(main_layout)

    def clear_layout(self, layout):
        try:
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
        except Exception as e:
            print(f"Error clearing layout: {e}")  # Debug print

    def show_email_otp_ui(self):
        self.clear_layout(self.form_layout)

        # --- Reset Password Form ---
        self.card_title = QLabel("Reset Password")
        self.card_title.setStyleSheet("color: #212529; margin-top: 5px;")
        self.card_title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.form_layout.addWidget(self.card_title)

        # Email
        self.email_label = QLabel("Email")
        self.email_label.setStyleSheet("color: #495057; margin-top: 5px;")
        self.form_layout.addWidget(self.email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter Email")
        self.email_input.setStyleSheet("border: 1px solid #ccc; border-radius: 6px; padding: 10px;")
        self.form_layout.addWidget(self.email_input)

        # OTP layout
        otp_layout = QVBoxLayout()
        otp_input_layout = QHBoxLayout()
        
        # OTP Input
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter OTP Code")
        self.otp_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 10px;
                margin-right: 10px;
            }
            QLineEdit:focus {
                border: 2px solid #006400;
            }
        """)
        
        # Send OTP Button
        self.send_otp_btn = QPushButton("Send OTP")
        self.send_otp_btn.setStyleSheet("""
            QPushButton {
                background-color: #006400;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                border: none;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton:hover:!disabled {
                background-color: #228B22;
            }
        """)
        self.send_otp_btn.clicked.connect(self.send_otp_clicked)
        
        # Resend OTP Button (initially hidden)
        self.resend_otp_btn = QPushButton("Resend OTP")
        self.resend_otp_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #006400;
                padding: 10px 5px;
                border: none;
                text-decoration: underline;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                color: #004d00;
            }
        """)
        self.resend_otp_btn.hide()
        self.resend_otp_btn.clicked.connect(self.send_otp_clicked)
        
        # Timer label
        self.otp_timer_label = QLabel("")
        self.otp_timer_label.setStyleSheet("color: #666666; font-style: italic;")
        
        # Add to layouts
        otp_input_layout.addWidget(self.otp_input)
        otp_input_layout.addWidget(self.send_otp_btn)
        
        otp_layout.addLayout(otp_input_layout)
        
        self.otp_button_layout = QHBoxLayout()
        self.otp_button_layout.addWidget(self.resend_otp_btn)
        self.otp_button_layout.addWidget(self.otp_timer_label)
        self.otp_button_layout.addStretch()
        
        otp_layout.addLayout(self.otp_button_layout)
        self.form_layout.addLayout(otp_layout)
        
        # OTP timer
        self.otp_timer = QTimer()
        self.otp_timer.timeout.connect(self.update_otp_timer)
        self.otp_seconds_left = 60  # 1 minute cooldown


        # Reset Password button
        self.reset_password_btn = QPushButton("Reset Password")
        self.reset_password_btn.setStyleSheet(
            "QPushButton { background-color: #006400; color: white; padding: 10px; "
            "border-radius: 6px; border: none; font-weight: bold; } "
            "QPushButton:hover { background-color: #228B22; }"
        )
        self.reset_password_btn.setMinimumHeight(38)
        self.form_layout.addWidget(self.reset_password_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.reset_password_btn.clicked.connect(self.validate_otp_and_proceed)
        
        # OTP validation error label
        self.otp_error_label = QLabel("")
        self.otp_error_label.setStyleSheet("color: red; margin-left: 5px;")
        self.form_layout.addWidget(self.otp_error_label)
        self.otp_error_label.hide()

    def show_change_password_ui(self):
        try:
            print("=== SHOW CHANGE PASSWORD UI STARTED ===")  # Debug print
            print("Current form_layout count:", self.form_layout.count())  # Debug print
            
            # Stop the OTP timer before clearing layout to prevent deleted object errors
            if hasattr(self, 'otp_timer') and self.otp_timer.isActive():
                print("Stopping OTP timer...")  # Debug print
                self.otp_timer.stop()
                print("OTP timer stopped successfully")  # Debug print
            
            # Store reference to prevent garbage collection issues
            self._current_form_widgets = []
            
            print("About to clear layout...")  # Debug print
            self.clear_layout(self.form_layout)
            print("Layout cleared successfully")  # Debug print
            
            # Add a debug timer to see if something is automatically closing the form
            print("Setting up debug timer to check form status...")  # Debug print
            QTimer.singleShot(1000, self.debug_form_status)
            QTimer.singleShot(3000, self.debug_form_status)
            
            # Add a keep-alive timer to prevent form from closing
            print("Setting up keep-alive timer...")  # Debug print
            self.keep_alive_timer = QTimer()
            self.keep_alive_timer.timeout.connect(self.keep_form_alive)
            self.keep_alive_timer.start(500)  # Check every 500ms

            # --- Change Password Form ---
            self.card_title = QLabel("Change Password")
            self.card_title.setStyleSheet("color: #212529; margin-top: 5px;")
            self.card_title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            self.form_layout.addWidget(self.card_title)

            # New Password
            self.new_password_label = QLabel("Enter New Password")
            self.new_password_label.setStyleSheet("color: #495057; margin-top: 5px;")
            self.form_layout.addWidget(self.new_password_label)

            self.new_password_input = QLineEdit()
            self.new_password_input.setPlaceholderText("Enter New Password")
            self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.new_password_input.setStyleSheet("border: 1px solid #ccc; border-radius: 6px; padding: 10px;")
            self.form_layout.addWidget(self.new_password_input)

            # Re-enter New Password
            self.reenter_password_label = QLabel("Re-enter New Password")
            self.reenter_password_label.setStyleSheet("color: #495057; margin-top: 5px;")
            self.form_layout.addWidget(self.reenter_password_label)

            self.reenter_password_input = QLineEdit()
            self.reenter_password_input.setPlaceholderText("Re-enter New Password")
            self.reenter_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.reenter_password_input.setStyleSheet("border: 1px solid #ccc; border-radius: 6px; padding: 10px;")
            self.form_layout.addWidget(self.reenter_password_input)

            # Error Label (initially hidden)
            self.error_label = QLabel("")
            self.error_label.setStyleSheet("color: red; margin-left: 5px;")
            self.form_layout.addWidget(self.error_label)
            self.error_label.hide()

            # Change Password button
            self.change_password_btn = QPushButton("Change Password")
            self.change_password_btn.setStyleSheet(
                "QPushButton { background-color: #006400; color: white; padding: 10px; "
                "border-radius: 6px; border: none; font-weight: bold; margin-top: 10px;} "
                "QPushButton:hover { background-color: #228B22; }"
            )
            self.change_password_btn.setMinimumHeight(38)
            self.change_password_btn.clicked.connect(self.validate_and_change_password)
            self.form_layout.addWidget(self.change_password_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
            # Success message label (initially hidden)
            self.success_label = QLabel("")
            self.success_label.setStyleSheet("color: #006400; font-weight: bold; margin-left: 5px;")
            self.form_layout.addWidget(self.success_label)
            self.success_label.hide()
            
            print("Change password UI created successfully")  # Debug print
            
            # Add a "Stay on this page" button to prevent accidental navigation
            stay_button = QPushButton("Stay on Password Reset Page")
            stay_button.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; padding: 8px; border-radius: 4px; margin-top: 10px; }")
            stay_button.clicked.connect(self.force_stay_on_page)
            self.form_layout.addWidget(stay_button, alignment=Qt.AlignmentFlag.AlignCenter)
            
        except Exception as e:
            print(f"ERROR creating change password UI: {e}")  # Debug print
            import traceback
            traceback.print_exc()  # Print full error traceback
            
            # Show error message
            error_label = QLabel("Error loading password reset form. Please try again.")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            self.form_layout.addWidget(error_label)
            
            # Add a back button to prevent getting stuck
            back_btn = QPushButton("Go Back to OTP")
            back_btn.setStyleSheet("QPushButton { background-color: #6c757d; color: white; padding: 8px; border-radius: 4px; }")
            back_btn.clicked.connect(self.show_email_otp_ui)
            self.form_layout.addWidget(back_btn)
    
    def debug_form_status(self):
        """Debug method to check form status"""
        try:
            print(f"=== DEBUG FORM STATUS ===")
            print(f"Form layout count: {self.form_layout.count()}")
            print(f"Widget visible: {self.isVisible()}")
            print(f"Parent widget: {self.parent()}")
            if hasattr(self, 'card_title'):
                print(f"Card title exists: {self.card_title.text()}")
            else:
                print("Card title does not exist")
        except Exception as e:
            print(f"Error in debug_form_status: {e}")
    
    def keep_form_alive(self):
        """Keep the form alive and prevent it from closing"""
        try:
            if hasattr(self, 'form_container') and self.form_container:
                if not self.form_container.isVisible():
                    print("Form container became invisible, making it visible again...")
                    self.form_container.show()
                
                # Force update the layout
                self.form_container.update()
                
                # Check if any critical widgets are missing
                if not hasattr(self, 'card_title') or not self.card_title:
                    print("Card title missing, recreating form...")
                    self.show_change_password_ui()
                    return
                    
                print("Form keep-alive check passed")
        except Exception as e:
            print(f"Error in keep_form_alive: {e}")
    
    def force_stay_on_page(self):
        """Force the form to stay on the current page"""
        print("=== FORCE STAY ON PAGE CALLED ===")
        try:
            # Ensure the form is visible
            if hasattr(self, 'form_container'):
                self.form_container.show()
                self.form_container.raise_()
            
            # Force update
            self.update()
            self.repaint()
            
            print("Form forced to stay visible")
            
            # Show a message to confirm
            if hasattr(self, 'success_label'):
                self.success_label.setText("Form is staying on this page!")
                self.success_label.show()
                
        except Exception as e:
            print(f"Error in force_stay_on_page: {e}")
    def send_otp_clicked(self):
        # Disable send button and start cooldown
        self.send_otp_btn.setEnabled(False)
        self.resend_otp_btn.hide()
        self.otp_timer_label.show()
        self.otp_seconds_left = 60
        self.update_otp_timer()
        self.otp_timer.start(1000)  # Update every second
        
        # Here you would typically send the OTP to the user's email
        # For now, we'll just show a success message
        self.show_otp_sent_message()
    
    def update_otp_timer(self):
        try:
            # Check if the timer label still exists before updating it
            if hasattr(self, 'otp_timer_label') and self.otp_timer_label and not self.otp_timer_label.isHidden():
                if self.otp_seconds_left > 0:
                    self.otp_timer_label.setText(f"Resend OTP in {self.otp_seconds_left} seconds")
                    self.otp_seconds_left -= 1
                else:
                    self.otp_timer.stop()
                    self.otp_timer_label.hide()
                    if hasattr(self, 'resend_otp_btn'):
                        self.resend_otp_btn.show()
            else:
                # Timer label doesn't exist or is hidden, stop the timer
                print("Timer label not found, stopping timer")  # Debug print
                self.otp_timer.stop()
        except Exception as e:
            print(f"Error in timer update: {e}")  # Debug print
            # Stop timer on error to prevent further issues
            if hasattr(self, 'otp_timer'):
                self.otp_timer.stop()
    
    def show_otp_sent_message(self):
        # Show success message
        if not hasattr(self, 'otp_success_label'):
            self.otp_success_label = QLabel("OTP has been sent to your email!")
            self.otp_success_label.setStyleSheet("color: #006400; font-weight: bold;")
            self.form_layout.insertWidget(3, self.otp_success_label)  # Insert after email input
        else:
            self.otp_success_label.show()
            
        # Auto-hide after 5 seconds
        QTimer.singleShot(5000, self.hide_otp_success_message)
    
    def hide_otp_success_message(self):
        if hasattr(self, 'otp_success_label'):
            self.otp_success_label.hide()
    
    def validate_otp_and_proceed(self):
        try:
            print("=== OTP VALIDATION STARTED ===")  # Debug print
            
            # Hide previous error messages
            self.otp_error_label.hide()
            
            # Get OTP input
            otp_input = self.otp_input.text().strip()
            print(f"OTP input received: '{otp_input}'")  # Debug print
            
            # Simple validation (you can replace this with actual OTP validation)
            if not otp_input:
                self.otp_error_label.setText("Please enter the OTP code.")
                self.otp_error_label.show()
                print("OTP validation failed: empty input")  # Debug print
                return
                
            if len(otp_input) < 4:
                self.otp_error_label.setText("OTP code must be at least 4 characters.")
                self.otp_error_label.show()
                print("OTP validation failed: too short")  # Debug print
                return
            
            # For demo purposes, accept any 4+ character OTP
            # In real implementation, validate against sent OTP
            print(f"OTP validated successfully: {otp_input}")  # Debug print
            print("About to call show_change_password_ui()")  # Debug print
            
            # Use QTimer to delay the UI change and prevent immediate crash
            QTimer.singleShot(100, self.show_change_password_ui)
            
        except Exception as e:
            print(f"ERROR in OTP validation: {e}")  # Debug print
            import traceback
            traceback.print_exc()  # Print full error traceback
            # Show error message instead of crashing
            self.otp_error_label.setText("An error occurred. Please try again.")
            self.otp_error_label.show()
    
    def validate_and_change_password(self):
        # Hide previous messages
        self.error_label.hide()
        self.success_label.hide()
        
        # Reset border styles
        base_style = "border: 1px solid #ccc; border-radius: 6px; padding: 10px;"
        error_style = "border: 2px solid red; border-radius: 6px; padding: 10px;"
        
        new_password = self.new_password_input.text().strip()
        reenter_password = self.reenter_password_input.text().strip()
        
        # Validation
        if not new_password:
            self.error_label.setText("New password is required.")
            self.error_label.show()
            self.new_password_input.setStyleSheet(error_style)
            return
            
        if len(new_password) < 6:
            self.error_label.setText("Password must be at least 6 characters long.")
            self.error_label.show()
            self.new_password_input.setStyleSheet(error_style)
            return
            
        if new_password != reenter_password:
            self.error_label.setText("Passwords do not match. Please re-enter correctly.")
            self.error_label.show()
            self.reenter_password_input.setStyleSheet(error_style)
            return
            
        # Reset border styles
        self.new_password_input.setStyleSheet(base_style)
        self.reenter_password_input.setStyleSheet(base_style)
        
        # Show success message
        self.success_label.setText("Password changed successfully! Redirecting to login...")
        self.success_label.show()
        
        # Clear inputs
        self.new_password_input.clear()
        self.reenter_password_input.clear()
        
        # Redirect to login after 2 seconds
        QTimer.singleShot(2000, self.request_back_to_signin)
    
    def request_back_to_signin(self, event=None):
        if hasattr(self, 'otp_timer') and self.otp_timer.isActive():
            self.otp_timer.stop()
        self.back_to_signin_requested.emit()
