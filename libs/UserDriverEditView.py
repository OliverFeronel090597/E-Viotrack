import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QSplitter
)
from PyQt6.QtCore import Qt

# Safe import
try:
    from libs.DatabaseConnector import DatabaseConnector
    from libs.UserTableWidget import UserTableWidget
    from libs.DriverTableWidget import DriverTableWidget
except ImportError:
    from DatabaseConnector import DatabaseConnector
    from UserTableWidget import UserTableWidget
    from DriverTableWidget import DriverTableWidget


# ==========================
# MAIN WINDOW SIDE BY SIDE
# ==========================
class UserDriver(QWidget):
    def __init__(self, db, notification_parent=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.notification_parent = notification_parent
        self.setWindowTitle("Admin Panel")
        self.resize(1200, 500)

        # Create a horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Add tables to the splitter
        self.user_table = UserTableWidget(db, self.notification_parent)
        self.driver_table = DriverTableWidget(db, self.notification_parent)
        splitter.addWidget(self.user_table)
        splitter.addWidget(self.driver_table)

        # Optional: initial width ratio
        splitter.setSizes([700, 500])

        # Prevent collapsing completely
        splitter.setChildrenCollapsible(False)

        # Use a layout to hold the splitter
        layout = QHBoxLayout()
        layout.addWidget(splitter)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = DatabaseConnector()
    window = UserDriver(db)
    window.show()
    sys.exit(app.exec())
