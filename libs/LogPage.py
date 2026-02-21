from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime
import sys


class StdoutRedirector(QObject):
    text_written = pyqtSignal(str)

    def write(self, text):
        if text:
            self.text_written.emit(text)

    def flush(self):
        pass


class LogPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("LogView")
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        self.setLayout(layout)

        # redirect stdout
        self._redirector = StdoutRedirector()
        self._redirector.text_written.connect(self._append_from_print)
        sys.stdout = self._redirector

        # optional initial log
        self.add_log("E-Viotrack Started")

    def _append_from_print(self, text: str):
        """Handle incoming text from #print() and push through add_log()."""
        for line in text.splitlines():
            if line.strip().startswith("$"):
                self.add_log(line.replace("$", ""))

    def add_log(self, text: str):
        """Append log text with timestamp and auto-scroll."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {text}"

        self.log_view.appendPlainText(log_line)
        self.log_view.moveCursor(QTextCursor.MoveOperation.End)