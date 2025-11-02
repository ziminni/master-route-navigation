from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsDropShadowEffect, QPushButton, QApplication, QHBoxLayout, QLabel, QStackedWidget, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import sys

# Relative imports from Academics to Classroom/Shared
try:
    from .Classroom.Shared.classroom_home import ClassroomHome
    from .Classroom.Shared.post_details import PostDetails
    from .ClassroomView import ClassroomView
    from frontend.controller.Academics.Classroom.classroom_controller import ClassroomController
except ImportError:
    try:
        from Classroom.Shared.classroom_home import ClassroomHome
        from Classroom.Shared.post_details import PostDetails
        from ClassroomView import ClassroomView
        from controller.classroom_controller import ClassroomController
    except ImportError:
        from views.Academics.Classroom.Shared.classroom_home import ClassroomHome
        from views.Academics.Classroom.Shared.post_details import PostDetails
        from views.Academics.ClassroomView import ClassroomView


class ClassroomMain(QWidget):
    """
    MAIN CLASSROOM CONTAINER - Central navigation hub for all classroom views
    - only one who uses stack widget
    - switches widgets with the help of signals
    
     NAVIGATION FLOW: 
    1. Home View (ClassroomHome) - shows class cards
       ↓ class_selected signal
    2. Classroom View (ClassroomView) - shows tabs (Stream, Classworks, etc.)
       ↓ post_selected signal
    3. Post Details View (PostDetails) - shows individual post content
       OR
       ↓ navigate_to_form signal  
    4. Form View (MaterialForm/AssessmentForm) - create new content

    SIGNAL CHAIN:
    ClassroomHome.class_selected → ClassroomMain.show_classroom
    ClassroomView.post_selected → ClassroomMain.show_post
    ClassroomView.navigate_to_form → ClassroomMain.show_form
    """
    
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.setMinimumSize(940, 530)
        self.setStyleSheet("background-color: white;")
        
        # Main layout - vertical for header + sidebar-content area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header (spans full width)
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background-color: white; 
                border-bottom: 1px solid #d0d0d0;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        header_title = QLabel("CLASSROOM")
        header_title.setFont(QFont("Poppins", 16, QFont.Weight.Bold))
        header_title.setStyleSheet("color: #1e5631;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # Content area (sidebar + main content)
        content_area = QWidget()
        content_area_layout = QHBoxLayout(content_area)
        content_area_layout.setContentsMargins(0, 0, 0, 0)
        content_area_layout.setSpacing(0)
        
        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(120)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #white;
                border-right: 1px solid #d0d0d0;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Sidebar buttons
        home_button = QPushButton("Home")
        home_button.setFixedHeight(50)
        home_button.setStyleSheet("""
            QPushButton {
                color: black;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        home_button.clicked.connect(self.show_home)
        sidebar_layout.addWidget(home_button)
        
        classes_button = QPushButton("Classes")
        classes_button.setFixedHeight(50)
        classes_button.setStyleSheet("""
            QPushButton {
                color: black;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        sidebar_layout.addWidget(classes_button)
        
        sidebar_layout.addStretch()
        
        # Main content area
        shadow = QGraphicsDropShadowEffect(blurRadius=20, xOffset=0, yOffset=3, color=QColor(0, 0, 0, 40))
        content_widget = QWidget()
        content_widget.setGraphicsEffect(shadow)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Stacked widget for dynamic content - manages view transitions
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: white;")
        
        # Initialize views
        self.classroom_controller = ClassroomController()
        self.home_view = ClassroomHome(username, roles, primary_role, token)
        self.current_classroom_view = None
        self.current_post_view = None
        self.current_form_view = None
        
        # Add home view as default
        self.stacked_widget.addWidget(self.home_view)
        
        # SIGNAL CONNECTION: Home → Classroom
        # When user clicks a class card in home view, navigate to classroom
        self.home_view.class_selected.connect(self.show_classroom)
        
        content_layout.addWidget(self.stacked_widget)
        
        # Add sidebar and content to content area
        content_area_layout.addWidget(sidebar)
        content_area_layout.addWidget(content_widget)
        
        # Add content area to main layout
        main_layout.addWidget(content_area)
        
        # Set initial view to home
        self.stacked_widget.setCurrentWidget(self.home_view)

    #methods for switching stack widget
    def show_classroom(self, cls):
        """
        NAVIGATION: Home → Classroom
        SIGNAL: ClassroomHome.class_selected → ClassroomMain.show_classroom
        DATA FLOW: class data (dict) passed from home to classroom view
        """
        print(f"📚 NAVIGATION: Home → Classroom ({cls['title']})")
        
        # Clean up previous classroom view to prevent memory leaks
        if self.current_classroom_view:
            self.stacked_widget.removeWidget(self.current_classroom_view)
            self.current_classroom_view.deleteLater()
        
        # Create new classroom view with the selected class data
        self.current_classroom_view = ClassroomView(cls, self.username, self.roles, self.primary_role, self.token)
        
        # SIGNAL CONNECTIONS: Set up navigation from classroom view
        # 1. Back to home
        self.current_classroom_view.back_clicked.connect(self.show_home)
        # 2. Show post details when post is clicked
        self.current_classroom_view.post_selected.connect(self.show_post)
        # 3. Show creation forms when faculty clicks "Create"
        self.current_classroom_view.navigate_to_form.connect(self.show_form)
        
        # Add to stacked widget and switch to it
        self.stacked_widget.addWidget(self.current_classroom_view)
        self.stacked_widget.setCurrentWidget(self.current_classroom_view)

    def show_form(self, form_type, cls):
        """
        NAVIGATION: Classroom → Form (Material/Assessment Creation)
        SIGNAL: ClassroomView.navigate_to_form → ClassroomMain.show_form
        DATA FLOW: form_type (str) and class data (dict) passed to form
        """
        print(f"📝 NAVIGATION: Classroom → {form_type.capitalize()} Form ({cls['title']})")
        
        # Clean up any existing form view
        if self.current_form_view:
            self.stacked_widget.removeWidget(self.current_form_view)
            self.current_form_view.deleteLater()
        
        # Create the appropriate form based on type
        if form_type == "material":
            from frontend.views.Academics.Classroom.Faculty.upload_materials import MaterialForm
            self.current_form_view = MaterialForm(
                cls=cls,
                username=self.username,
                roles=self.roles,
                primary_role=self.primary_role,
                token=self.token,
                post_controller=self.current_classroom_view.classworks_view.post_controller if self.current_classroom_view else None
            )
        elif form_type == "assessment":
            from frontend.views.Academics.Classroom.Faculty.create_assessment import AssessmentForm
            self.current_form_view = AssessmentForm(
                cls=cls,
                username=self.username,
                roles=self.roles,
                primary_role=self.primary_role,
                token=self.token,
                post_controller=self.current_classroom_view.classworks_view.post_controller if self.current_classroom_view else None
            )
        else:
            print(f"Unknown form type: {form_type}")
            return
        
        # SIGNAL CONNECTION: Form → Classroom
        # When user clicks back in form, return to classroom view
        self.current_form_view.back_clicked.connect(self.return_to_classroom_from_form)

        if hasattr(self.current_form_view, 'material_created'):
            self.current_form_view.material_created.connect(self.refresh_classroom_views)
        
        # Add form to stacked widget and show it
        self.stacked_widget.addWidget(self.current_form_view)
        self.stacked_widget.setCurrentWidget(self.current_form_view)

    def refresh_classroom_views(self):
        """Refresh both stream and classworks when new material is created"""
        if self.current_classroom_view:
            self.current_classroom_view.stream_view.refresh_posts()
            self.current_classroom_view.classworks_view.refresh_posts()

    def return_to_classroom_from_form(self):
        """
        NAVIGATION: Form → Classroom (Back navigation)
        SIGNAL: MaterialForm/AssessmentForm.back_clicked → ClassroomMain.return_to_classroom_from_form
        """
        print("🔙 NAVIGATION: Form → Classroom (Back from form)")
        if self.current_form_view:
            self.stacked_widget.removeWidget(self.current_form_view)
            self.current_form_view.deleteLater()
            self.current_form_view = None
        
        # Return to the classroom view that was active before form
        if self.current_classroom_view:
            self.stacked_widget.setCurrentWidget(self.current_classroom_view)
    
    def show_post(self, post):
        """
        NAVIGATION: Classroom → Post Details
        SIGNAL: ClassroomView.post_selected → ClassroomMain.show_post
        DATA FLOW: post data (dict) passed to post details view
        TRIGGER: User clicks on any post in Stream or Classworks view
        """
        print(f"NAVIGATION: Classroom → Post Details ({post['title']})")
        
        # Clean up previous post view
        if self.current_post_view:
            self.stacked_widget.removeWidget(self.current_post_view)
            self.current_post_view.deleteLater()
        
        # FIXED: Create post details view with all required parameters
        self.current_post_view = PostDetails(
            post=post,
            username=self.username,
            roles=self.roles,
            primary_role=self.primary_role,
            parent=self
        )
        
        # SIGNAL CONNECTION: Post Details → Classroom
        # When user clicks back in post details, return to classroom
        self.current_post_view.back_clicked.connect(self.return_to_classroom)
        # Connect edit and delete signals
        self.current_post_view.post_edited.connect(self.handle_post_edit)
        self.current_post_view.post_deleted.connect(self.handle_post_delete)
        # NEW: Connect syllabus deletion signal
        self.current_post_view.syllabus_deleted.connect(self.handle_syllabus_delete)
        
        self.stacked_widget.addWidget(self.current_post_view)
        self.stacked_widget.setCurrentWidget(self.current_post_view)


    def handle_post_edit(self, post):
        """Handle post edit from PostDetails"""
        print(f"Editing post: {post['title']}")
        # TODO: Implement edit functionality
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Edit Post", f"Edit functionality for '{post['title']}' will be implemented soon.")

    def handle_syllabus_delete(self, syllabus_post):
        """Handle syllabus deletion from PostDetails"""
        print(f"Deleting syllabus: {syllabus_post['title']}")
        
        # Create confirmation dialog
        reply = QMessageBox(self)
        reply.setWindowTitle("Delete Post")
        reply.setText(f"Are you sure you want to delete '{syllabus_post['title']}'?")
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
            # Delete syllabus using post_controller
            if self.current_classroom_view and hasattr(self.current_classroom_view, 'classworks_view'):
                post_controller = self.current_classroom_view.classworks_view.post_controller
                
                # Delete syllabus from the service
                if hasattr(post_controller, 'delete_syllabus'):
                    if post_controller.delete_syllabus():
                        print("Syllabus deleted successfully")
                        
                        # Show success message
                        QMessageBox.information(self, "Success", "Syllabus deleted successfully.")
                        
                        # Refresh all views and go back to class content
                        self.refresh_classroom_views()
                        self.return_to_classroom()
                    else:
                        print("Failed to delete syllabus")
                        QMessageBox.warning(self, "Error", "Failed to delete syllabus. Please try again.")
                else:
                    print("Syllabus deletion not implemented in controller")
                    QMessageBox.warning(self, "Error", "Syllabus deletion is not yet implemented.")
            else:
                print("No post controller available")
                QMessageBox.warning(self, "Error", "Cannot delete syllabus: No classroom view available.")

    def handle_post_delete(self, post):
        """Handle post delete from PostDetails"""
        print(f"Deleting post: {post['title']}")
        print(f"DEBUG: Post data - id: {post.get('id')}, post_id: {post.get('post_id')}")
        
        # Debug: Print all posts for this class
        if self.current_classroom_view and hasattr(self.current_classroom_view, 'classworks_view'):
            post_controller = self.current_classroom_view.classworks_view.post_controller
            # Call debug method to see what posts exist
            if hasattr(post_controller.post_service, 'debug_print_posts'):
                post_controller.post_service.debug_print_posts(post_controller.current_class_id)
        
        # Create confirmation dialog - FIXED: QMessageBox is now imported
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
            # Use your post_controller to delete the post
            if self.current_classroom_view and hasattr(self.current_classroom_view, 'classworks_view'):
                post_controller = self.current_classroom_view.classworks_view.post_controller
                
                # Try both possible ID fields
                post_id_to_delete = post.get('id') or post.get('post_id')
                
                if post_id_to_delete and post_controller.delete_post(post_id_to_delete):
                    print("Post deleted successfully")
                    
                    # Show success message
                    QMessageBox.information(self, "Success", f"Post '{post['title']}' deleted successfully.")
                    
                    # Refresh all views and go back to class content
                    self.refresh_classroom_views()
                    self.return_to_classroom()
                else:
                    print("Failed to delete post")
                    QMessageBox.warning(self, "Error", "Failed to delete post. Please try again.")
            else:
                print("No post controller available")
                QMessageBox.warning(self, "Error", "Cannot delete post: No classroom view available.")

    def refresh_classroom_views(self):
        """Refresh all classroom views after post deletion"""
        if self.current_classroom_view:
            # Refresh stream view
            if hasattr(self.current_classroom_view, 'stream_view'):
                self.current_classroom_view.stream_view.refresh_posts()
            
            # Refresh classworks view  
            if hasattr(self.current_classroom_view, 'classworks_view'):
                self.current_classroom_view.classworks_view.refresh_posts()
    
    def return_to_classroom(self):
        """
        NAVIGATION: Post Details → Classroom (Back navigation)
        SIGNAL: PostDetails.back_clicked → ClassroomMain.return_to_classroom
        """
        print("🔙 NAVIGATION: Post Details → Classroom (Back from post)")
        if self.current_post_view:
            self.stacked_widget.removeWidget(self.current_post_view)
            self.current_post_view.deleteLater()
            self.current_post_view = None
        
        # Return to the classroom view that was active before post details
        if self.current_classroom_view:
            self.stacked_widget.setCurrentWidget(self.current_classroom_view)
    
    def show_home(self):
        """
        NAVIGATION: Any View → Home (Global back navigation)
        SIGNAL: Various views.back_clicked → ClassroomMain.show_home
        TRIGGER: User clicks back button in classroom view or sidebar home button
        """
        print("NAVIGATION: Any → Home (Global back)")
        
        # Clean up classroom view if it exists
        if self.current_classroom_view:
            self.stacked_widget.removeWidget(self.current_classroom_view)
            self.current_classroom_view.deleteLater()
            self.current_classroom_view = None
        
        # Always return to home view
        self.stacked_widget.setCurrentWidget(self.home_view)
        

def main():
    app = QApplication(sys.argv)
    window = ClassroomMain()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()