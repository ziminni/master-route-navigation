# classroom_stream.py
from PyQt6.QtWidgets import QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout, QPushButton,QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from widgets.Academics.stream_post_ui import Ui_ClassroomStreamContent
from utils.date_utils import format_date_display

class ClassroomStream(QWidget):
    post_selected = pyqtSignal(dict)
    post_created = pyqtSignal()  # Add this signal

    def __init__(self, cls, username, roles, primary_role, token, post_controller, parent=None):
        super().__init__(parent)
        self.cls = cls
        self.post_controller = post_controller
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Setup the UI from the .ui file
        self.ui = Ui_ClassroomStreamContent()
        self.ui.setupUi(self)
        
        # Set class information in the header
        self.setup_class_info()
        
        # Setup the existing template widgets
        self.setup_existing_widgets()
        
        self.load_posts()
        self.load_syllabus() 

    def setup_existing_widgets(self):
        """Setup the existing template widgets"""
        # Hide syllabus frame initially - we'll show it only if syllabus exists
        if hasattr(self.ui, 'syllabusFrame') and self.ui.syllabusFrame:
            self.ui.syllabusFrame.setVisible(False)
        
        # Hide the template post initially
        if hasattr(self.ui, 'postTemplate') and self.ui.postTemplate:
            self.ui.postTemplate.setVisible(False)

    def load_syllabus(self):

        """Load and display syllabus if it exists"""
        syllabus = self.post_controller.get_syllabus()
        print(f"Syllabus found: {syllabus is not None}")
        
        if hasattr(self.ui, 'syllabusFrame') and self.ui.syllabusFrame:
            if syllabus:
                # Syllabus exists - show and setup the frame
                self.ui.syllabusFrame.setVisible(True)
                
                # Update syllabus text
                if hasattr(self.ui, 'label_2') and self.ui.label_2:
                    self.ui.label_2.setText(syllabus.get("title", "Syllabus"))
                
                # Reconnect view button
                if hasattr(self.ui, 'pushButton') and self.ui.pushButton:
                    try:
                        self.ui.pushButton.clicked.disconnect()
                    except:
                        pass
                    self.ui.pushButton.setText("View")
                    # FIX: Use lambda without parameters or use partial
                    self.ui.pushButton.clicked.connect(lambda: self.on_syllabus_click(syllabus))
                
                # Make entire frame clickable - FIX: use proper lambda
                self.ui.syllabusFrame.mousePressEvent = lambda event: self.handle_syllabus_click(event, syllabus)
                self.ui.syllabusFrame.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                # No syllabus - hide the frame
                self.ui.syllabusFrame.setVisible(False)

    def on_syllabus_click(self, syllabus):
        """Handle syllabus view button click"""
        # Convert syllabus to post-like format for PostDetails
        post_like_syllabus = {
            "id": f"syllabus_{syllabus.get('id', '')}",
            "title": syllabus.get("title", "Syllabus"),
            "content": syllabus.get("content", ""),
            "author": syllabus.get("author", ""),
            "date": syllabus.get("date", ""),
            "type": "syllabus"  # Special type for syllabus
        }
        self.post_selected.emit(post_like_syllabus)

    def handle_syllabus_click(self, event, syllabus):
        """Handle clicking on syllabus frame"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_syllabus_click(syllabus)  # This should work now

    def refresh_syllabus(self):
        """Refresh syllabus display (called after creation)"""
        print("Refreshing syllabus in stream...")
        self.load_syllabus()

    def setup_class_info(self):
        """Set the class information in the header"""
        self.ui.courseCode_label.setText(self.cls.get("code", ""))
        self.ui.courseTitle_label.setText(self.cls.get("title", ""))
        section_text = f"{self.cls.get('section', '')}\n{self.cls.get('schedule', '')}"
        self.ui.courseSection_label.setText(section_text)

    def setup_existing_widgets(self):
        """Setup the existing syllabus frame and template post"""
        # Setup syllabus frame
        if hasattr(self.ui, 'syllabusFrame') and self.ui.syllabusFrame:
            # Update syllabus text if needed
            if hasattr(self.ui, 'label_2') and self.ui.label_2:
                self.ui.label_2.setText("Syllabus")
            if hasattr(self.ui, 'pushButton') and self.ui.pushButton:
                self.ui.pushButton.setText("View")
                # Connect syllabus button click
                self.ui.pushButton.clicked.connect(self.on_syllabus_click)
        
        # Hide the template post initially (we'll use it as a template)
        if hasattr(self.ui, 'postTemplate') and self.ui.postTemplate:
            self.ui.postTemplate.setVisible(False)

    def on_syllabus_click(self, syllabus=None):
        """Handle syllabus view button click"""
        # If syllabus is not passed, try to get it from controller
        if syllabus is None:
            syllabus = self.post_controller.get_syllabus()
        
        if syllabus:
            # Convert syllabus to post-like format for PostDetails
            post_like_syllabus = {
                "id": f"syllabus_{syllabus.get('id', '')}",
                "title": syllabus.get("title", "Syllabus"),
                "content": syllabus.get("content", ""),
                "author": syllabus.get("author", ""),
                "date": syllabus.get("date", ""),
                "type": "syllabus"  # Special type for syllabus
            }
            self.post_selected.emit(post_like_syllabus)

    def load_posts(self):
        # Use PostController to get posts (they're already sorted by the service)
        posts = self.post_controller.get_stream_posts()
        print(f"Loading {len(posts)} posts in stream")
        
        # Get the stream items layout
        stream_layout = self.get_stream_layout()
        if not stream_layout:
            print("Error: Could not find stream layout!")
            return
        
        # Clear existing posts (except the template)
        self.clear_stream_layout(stream_layout)
        
        if not posts:
            no_posts_label = QLabel("No posts available")
            no_posts_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 14px;
                    padding: 20px;
                    text-align: center;
                }
            """)
            stream_layout.addWidget(no_posts_label)
            return
        
        # Add regular posts (excluding syllabus which is handled separately)
        regular_posts = [p for p in posts if p.get("title") != "Syllabus"]
        for post in regular_posts:
            self.create_post_widget(post, stream_layout)

    def get_stream_layout(self):
        """Find the correct stream layout from the UI structure"""
        try:
            # The stream items layout is in: scrollArea -> scrollAreaWidgetContents -> verticalLayout_5 -> horizontalLayout_5 -> stream_item_container -> verticalLayout_6 -> stream_items_layout
            if (hasattr(self.ui, 'scrollArea') and self.ui.scrollArea and
                hasattr(self.ui, 'scrollAreaWidgetContents') and self.ui.scrollAreaWidgetContents):
                
                # Try to find the stream_items_layout
                stream_container = self.ui.scrollAreaWidgetContents.findChild(QWidget, "stream_item_container")
                if stream_container:
                    stream_layout = stream_container.findChild(QVBoxLayout, "stream_items_layout")
                    if stream_layout:
                        return stream_layout
                
                # Fallback: try to access directly through attributes
                if hasattr(self.ui, 'stream_items_layout'):
                    return self.ui.stream_items_layout
                    
        except Exception as e:
            print(f"Error finding stream layout: {e}")
        
        # Ultimate fallback: create a new layout
        print("Creating fallback layout")
        fallback_widget = QWidget()
        fallback_layout = QVBoxLayout(fallback_widget)
        self.ui.scrollArea.setWidget(fallback_widget)
        return fallback_layout

    def clear_stream_layout(self, stream_layout):
        """Clear the stream layout while preserving the template"""
        if not stream_layout:
            return
            
        # Remove all widgets except the template
        for i in range(stream_layout.count() - 1, -1, -1):
            item = stream_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Don't remove the template post
                if widget != getattr(self.ui, 'postTemplate', None):
                    widget.setParent(None)
                    widget.deleteLater()


    def create_post_widget(self, post, stream_layout):
        """Create a post widget based on the template with proper spacing and document icon"""
        try:
            # Use the template as a base if it exists
            if hasattr(self.ui, 'postTemplate') and self.ui.postTemplate:
                # Clone the template structure
                post_frame = QFrame()
                post_frame.setStyleSheet(self.ui.postTemplate.styleSheet())
                post_frame.setFrameShape(self.ui.postTemplate.frameShape())
                post_frame.setFrameShadow(self.ui.postTemplate.frameShadow())
                
                # Create the same layout structure with better spacing
                layout = QHBoxLayout(post_frame)
                layout.setContentsMargins(15, 12, 15, 12)  # Increased padding
                layout.setSpacing(15)  # Increased spacing between icon and content
                
                # Icon with document.svg
                icon_label = QLabel()
                icon_label.setFixedSize(42, 42)  # Fixed size instead of maximum
                icon_label.setStyleSheet("""
                    QLabel {
                        background-color: #084924;
                        border-radius: 23px;
                        border: 2px solid white;
                        min-width: 42px;
                        min-height: 42px;
                    }
                """)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Load and set the document icon
                try:
                    from PyQt6.QtGui import QPixmap
                    icon_path = "frontend/assets/icons/document.svg"
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        # Scale the icon to fit within the circle
                        scaled_pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, 
                                                    Qt.TransformationMode.SmoothTransformation)
                        icon_label.setPixmap(scaled_pixmap)
                    else:
                        # Fallback: use text if icon not found
                        icon_label.setText("📄")
                        icon_label.setStyleSheet(icon_label.styleSheet() + """
                            QLabel {
                                color: white;
                                font-size: 16px;
                            }
                        """)
                except Exception as icon_error:
                    print(f"Error loading icon: {icon_error}")
                    # Fallback to text icon
                    icon_label.setText("📄")
                    icon_label.setStyleSheet(icon_label.styleSheet() + """
                        QLabel {
                            color: white;
                            font-size: 16px;
                        }
                    """)
                
                layout.addWidget(icon_label)
                
                # Content area with proper spacing
                content_layout = QVBoxLayout()
                content_layout.setSpacing(8)  # Increased spacing between title and date
                content_layout.setContentsMargins(0, 0, 0, 0)
                
                # Title ONLY - no author mentioned
                title = post.get("title", "")
                title_label = QLabel(title)
                title_label.setStyleSheet("""
                    QLabel {
                        font-size: 16px;
                        border: none;
                        color: #333;
                        margin: 0px;
                        padding: 0px;
                    }
                """)
                title_label.setWordWrap(True)
                title_label.setMinimumHeight(20)  # Ensure minimum height
                title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                content_layout.addWidget(title_label)
                
                # Date
                date_text = self.format_date(post.get("date", ""))
                date_label = QLabel(date_text)
                date_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        border: none;
                        color: #666;
                        margin: 0px;
                        padding: 0px;
                    }
                """)
                date_label.setMinimumHeight(16)  # Ensure minimum height
                content_layout.addWidget(date_label)
                
                # Add stretch to push content to top and prevent squishing
                content_layout.addStretch()
                
                layout.addLayout(content_layout)
                layout.addStretch()
                
                # Add menu button for faculty/admin (same as Classworks)
                if self.primary_role in ["faculty", "admin"]:
                    menu_button = QPushButton("⋮")
                    menu_button.setFixedSize(30, 30)
                    from PyQt6.QtGui import QFont
                    menu_font = QFont("Poppins")
                    menu_font.setPointSize(16)
                    menu_button.setFont(menu_font)
                    menu_button.setStyleSheet("""
                        QPushButton {
                            border: none;
                            background-color: transparent;
                            color: #656d76;
                            border-radius: 15px;
                            font-weight: bold;
                            font-family: "Poppins", Arial, sans-serif;
                        }
                        QPushButton:hover {
                            background-color: #F3F4F6;
                        }
                    """)
                    layout.addWidget(menu_button)
                    
                    # Connect menu button click
                    menu_button.clicked.connect(lambda checked, p=post: self.show_post_menu(p, menu_button))
                
                # Make clickable
                post_frame.mousePressEvent = lambda event, p=post: self.handle_post_click(event, p)
                post_frame.setCursor(Qt.CursorShape.PointingHandCursor)
                
                stream_layout.addWidget(post_frame)
                
            else:
                # Fallback: simple widget
                self.create_simple_post_widget(post, stream_layout)
                
        except Exception as e:
            print(f"Error creating post widget: {e}")
            # Fallback to simple widget
            self.create_simple_post_widget(post, stream_layout)
                    
        except Exception as e:
            print(f"Error creating post widget: {e}")
            # Fallback to simple widget
            self.create_simple_post_widget(post, stream_layout)

    def show_post_menu(self, post, menu_button):
        """Show context menu for post actions (Edit, Delete)"""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 0px;
                font-family: "Poppins", Arial, sans-serif;
            }
            QMenu::item {
                padding: 8px 16px;
                font-size: 16px;
            }
            QMenu::item:selected {
                background-color: #f5f5f5;
            }
        """)
        
        edit_action = QAction("Edit", self)
        delete_action = QAction("Delete", self)
        
        edit_action.triggered.connect(lambda: self.edit_post(post))
        delete_action.triggered.connect(lambda: self.delete_post(post))
        
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        button_pos = menu_button.mapToGlobal(menu_button.rect().bottomLeft())
        menu.exec(button_pos)

    def edit_post(self, post):
        """Handle edit post action"""
        print(f"Edit post: {post['title']}")
        # TODO: Implement edit post functionality
        # You can emit a signal or open an edit dialog here

    def delete_post(self, post):
        """Handle delete post action"""
        print(f"Delete post: {post['title']}")
        
        # Import QMessageBox here to avoid circular imports
        from PyQt6.QtWidgets import QMessageBox
        
        # Create confirmation dialog
        reply = QMessageBox(self)
        reply.setWindowTitle("Delete Post")
        reply.setText(f"Are you sure you want to delete '{post['title']}'?")
        reply.setIcon(QMessageBox.Icon.Question)
        reply.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No
        )
        reply.setDefaultButton(QMessageBox.StandardButton.No)
        
        # Apply styling to match the app
        reply.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-family: "Poppins", Arial, sans-serif;
            }
            QMessageBox QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-family: "Poppins", Arial, sans-serif;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1B5E20;
            }
        """)
        
        result = reply.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            # Delete the post using post_controller
            if self.post_controller.delete_post(post["id"]):
                print("Post deleted successfully")
                
                # Refresh both Stream and Classworks views
                self.refresh_posts()
                
                # Also refresh Classworks view if it exists
                if hasattr(self, 'classworks_view_ref'):
                    self.classworks_view_ref.refresh_posts()
                else:
                    # Try to find classworks view through parent
                    parent = self.parent()
                    while parent:
                        if hasattr(parent, 'classworks_view'):
                            parent.classworks_view.refresh_posts()
                            break
                        parent = parent.parent()
            else:
                print("Failed to delete post")
                QMessageBox.warning(self, "Error", "Failed to delete post. Please try again.")

    def set_classworks_reference(self, classworks_view):
        """Set reference to Classworks view for cross-refresh"""
        self.classworks_view_ref = classworks_view
        
    def create_simple_post_widget(self, post, stream_layout):
        """Create a simple post widget as fallback with proper spacing and icon"""
        try:
            # Create a frame instead of just a QLabel for better layout control
            post_frame = QFrame()
            post_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    margin: 5px;
                }
            """)
            
            layout = QHBoxLayout(post_frame)
            layout.setContentsMargins(12, 8, 12, 8)
            layout.setSpacing(10)
            
            # Icon with document.svg
            icon_label = QLabel()
            icon_label.setFixedSize(30, 30)
            icon_label.setStyleSheet("""
                QLabel {
                    background-color: #084924;
                    border-radius: 15px;
                    border: 2px solid white;
                }
            """)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Load and set the document icon
            try:
                from PyQt6.QtGui import QPixmap
                icon_path = "frontend/assets/icons/document.svg"
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, 
                                                Qt.TransformationMode.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
                else:
                    icon_label.setText("📄")
                    icon_label.setStyleSheet(icon_label.styleSheet() + """
                        QLabel {
                            color: white;
                            font-size: 12px;
                        }
                    """)
            except Exception as icon_error:
                icon_label.setText("📄")
                icon_label.setStyleSheet(icon_label.styleSheet() + """
                    QLabel {
                        color: white;
                        font-size: 12px;
                    }
                """)
            
            layout.addWidget(icon_label)
            
            # Content area
            content_layout = QVBoxLayout()
            content_layout.setSpacing(4)
            content_layout.setContentsMargins(0, 0, 0, 0)
            
            # Title only
            title_label = QLabel(post.get('title', ''))
            title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            title_label.setWordWrap(True)
            title_label.setMinimumHeight(18)
            content_layout.addWidget(title_label)
            
            # Date
            date_label = QLabel(self.format_date(post.get('date', '')))
            date_label.setStyleSheet("font-size: 12px; color: #666;")
            date_label.setMinimumHeight(14)
            content_layout.addWidget(date_label)
            
            layout.addLayout(content_layout, 1)  # Set stretch factor
            
            # Add menu button for faculty/admin
            if self.primary_role in ["faculty", "admin"]:
                menu_button = QPushButton("⋮")
                menu_button.setFixedSize(30, 30)
                from PyQt6.QtGui import QFont
                menu_font = QFont("Poppins")
                menu_font.setPointSize(16)
                menu_button.setFont(menu_font)
                menu_button.setStyleSheet("""
                    QPushButton {
                        border: none;
                        background-color: transparent;
                        color: #656d76;
                        border-radius: 15px;
                        font-weight: bold;
                        font-family: "Poppins", Arial, sans-serif;
                    }
                    QPushButton:hover {
                        background-color: #F3F4F6;
                    }
                """)
                layout.addWidget(menu_button)
                
                # Connect menu button click
                menu_button.clicked.connect(lambda checked, p=post: self.show_post_menu(p, menu_button))
            
            layout.addStretch()
            
            post_frame.mousePressEvent = lambda event, p=post: self.handle_post_click(event, p)
            post_frame.setCursor(Qt.CursorShape.PointingHandCursor)
            stream_layout.addWidget(post_frame)
            
        except Exception as e:
            print(f"Error creating simple post widget: {e}")

        # In classroom_stream.py
    def set_classworks_reference(self, classworks_view):
        self.classworks_view = classworks_view

        # Add this method to ensure proper refresh
    def refresh_posts(self):
        """Force refresh posts from controller"""
        self.load_posts()
        self.load_syllabus()

    def refresh_syllabus(self):
        """Refresh syllabus display (called after creation)"""
        print("Refreshing syllabus in stream...")
        try:
            self.load_syllabus()
            # Also force a layout update
            if hasattr(self.ui, 'syllabusFrame'):
                self.ui.syllabusFrame.update()
                self.ui.syllabusFrame.repaint()
        except Exception as e:
            print(f"Error refreshing syllabus: {e}")

    def refresh_all(self):
        """Refresh both posts and syllabus"""
        self.refresh_posts()
        self.refresh_syllabus()
        
    # Also update the set_classworks_reference method:
    def set_classworks_reference(self, classworks_view):
        self.classworks_view = classworks_view
        # Also set up bidirectional reference
        classworks_view.stream_view = self


    def format_date(self, date_str):
        return format_date_display(date_str)
    
    def handle_post_click(self, event, post):
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"Stream post clicked: {post['title']}")
            self.post_selected.emit(post)

    def clear(self):
        """Clear the stream layout"""
        stream_layout = self.get_stream_layout()
        if stream_layout:
            self.clear_stream_layout(stream_layout)