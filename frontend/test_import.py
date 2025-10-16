# test_import.py

from views.Messaging.launcher import MainChatWidget
from PyQt6.QtWidgets import QApplication
from views.Messaging.launcher import MainChatWidget
import sys

def main():
    widget = MainChatWidget()
    print("MainChatWidget instantiated successfully:", widget)
    

app = QApplication(sys.argv)   # Create QApplication first
widget = MainChatWidget()      # Now create your widget
widget.show()                  # Show the widget (optional but common)

sys.exit(app.exec())           # Start the app event loop


if __name__ == "__main__":
    main()
