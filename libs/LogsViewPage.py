from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QMessageBox, QScrollArea, QHBoxLayout
)
from PyQt6.QtCore import Qt, QSettings
from libs.DatabaseConnector import DatabaseConnector
from libs.SerialWidget import SerialWidget


# ---------------- HOME PAGE WITH HORIZONTAL SCROLL ----------------
class LogsViewPage(QWidget):
    MAX_WIDGETS = 4

    def __init__(self, db: DatabaseConnector):
        super().__init__()
        self.db = db
        self.widgets = []

        self.settings = QSettings("MyCompany", "RFIDApp")  # store widget count
        self.last_count = self.settings.value("widget_count", 1, type=int)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.title_label = QLabel("RFID Driver Violations")
        self.title_label.setObjectName("TitleLabel")
        layout.addWidget(self.title_label)

        # Scrollable horizontal container
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.widget_layout = QHBoxLayout(scroll_content)
        scroll_content.setLayout(self.widget_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Add button
        self.add_button = QPushButton("+ Add RFID Widget")
        self.add_button.clicked.connect(self.add_widget)
        layout.addWidget(self.add_button)

        # Restore previous widget count
        for _ in range(min(self.last_count, self.MAX_WIDGETS)):
            self.add_widget()

    def add_widget(self):
        if len(self.widgets) >= self.MAX_WIDGETS:
            QMessageBox.warning(self, "Limit Reached", "Maximum 4 widgets allowed")
            return

        widget = SerialWidget(self.db, remove_callback=self.remove_widget)
        self.widgets.append(widget)
        self.widget_layout.addWidget(widget)
        self.settings.setValue("widget_count", len(self.widgets))

    def remove_widget(self, widget: SerialWidget):
        if widget in self.widgets:
            self.widgets.remove(widget)
            self.settings.setValue("widget_count", len(self.widgets))
