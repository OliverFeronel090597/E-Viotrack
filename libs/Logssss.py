from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt
from libs.DatabaseConnector import DatabaseConnector
from libs.SerialReaderThread import SerialReaderThread
from libs.SerialWidget import SerialWidget
from libs.LogsViewPage import LogsViewPage
import sys


# For backward compatibility, export LogsViewPage as HomePage
HomePage = LogsViewPage

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    db = DatabaseConnector()
    window = LogsViewPage(db)
    window.show()
    sys.exit(app.exec())

