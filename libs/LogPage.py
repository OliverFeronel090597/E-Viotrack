from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtGui import QTextCursor
from datetime import datetime


class LogPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Installer Log Example")
        self.setObjectName("LogWindow")

        layout = QVBoxLayout()

        # Log viewer
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("LogView")
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        self.setLayout(layout)

        self.add_log("E-Viotrack Started")

    def add_log(self, text: str):
        """Append log text with timestamp and auto-scroll."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {text}"

        self.log_view.appendPlainText(log_line)
        self.log_view.moveCursor(QTextCursor.MoveOperation.End)
