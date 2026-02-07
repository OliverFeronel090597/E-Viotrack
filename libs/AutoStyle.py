from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QFile

class StylesheetModifier:
    def __init__(self, qss_path: str, parent: QWidget, interval_ms: int = 1000):
        self.qss_path = qss_path
        self.parent = parent

        self.timer = QTimer(parent)
        self.timer.timeout.connect(self.apply_stylesheet)
        self.timer.start(interval_ms)

        self.apply_stylesheet()

    def apply_stylesheet(self):
        file = QFile(self.qss_path)
        if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            content = file.readAll().data().decode()
            self.parent.setStyleSheet(content)
            file.close()
