from PyQt6.QtWidgets import QFileDialog

class ClassMaterialController:
    def __init__(self, view):
        """Initialize the controller with the view (UploadClassMaterialPanel)."""
        print("Controller initialized")
        self.view = view
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots, ensuring no duplicate connections."""
        if hasattr(self.view, 'browse_btn'):
            # Disconnect any existing connections to avoid duplicates
            try:
                self.view.browse_btn.clicked.disconnect(self.on_browse_clicked)
            except TypeError:
                pass  # Ignore if no connection exists yet
            self.view.browse_btn.clicked.connect(self.on_browse_clicked)
            print("Browse button connected")  # Debug print

    def on_browse_clicked(self):
        """Handle the browse button click to open a file selection dialog."""
        print("Opening file dialog")  # Debug print
        file_dialog = QFileDialog(self.view)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)  # Select a single existing file
        file_dialog.setNameFilter("All Files (*);;PDF Files (*.pdf);;Word Documents (*.docx)")  # Optional filters
        file_dialog.setViewMode(QFileDialog.ViewMode.List)  # Display as list

        print("on_browsed_clicked method called")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                for file_path in selected_files: 
                    print(f"Selected file: {file_path}") 
        else: 
            print("Dialog closed") 

    def connect_browse_button(self, button):
        """Connect the browse button signal if not already connected."""
        if button and hasattr(self, 'view') and self.view.browse_btn == button:
            self.connect_signals()  # Reconnect if needed