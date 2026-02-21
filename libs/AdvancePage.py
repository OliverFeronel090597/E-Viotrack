import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QSplitter
)
from PyQt6.QtCore import Qt


from libs.DatabaseConnector import DatabaseConnector
from libs.ViolationTypeTableWidget import ViolationTypeTableWidget
from libs.ViolationTableWidget import ViolationTableWidget
from libs.Homepage import HomePage


# ==========================
# MAIN WINDOW
# ==========================
class AdvancePage(QWidget):
    def __init__(self, db: DatabaseConnector, home_update:HomePage, parent=None):
        super().__init__(parent)
        self.db = db
        self.source_parent = parent
        self.home_update = home_update

        # Use a horizontal splitter instead of a simple layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Add widgets to splitter
        self.violation_table = ViolationTableWidget(db, self.home_update, parent=self)
        self.violation_type_table = ViolationTypeTableWidget(db, parent=self)
        splitter.addWidget(self.violation_table)
        splitter.addWidget(self.violation_type_table)

        # Optional: set initial sizes (ratio)
        splitter.setSizes([900, 300])  # initial pixel width

        # Optional: allow user to resize freely
        splitter.setChildrenCollapsible(False)

        # Set splitter as main layout
        layout = QHBoxLayout()
        layout.addWidget(splitter)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        
    def show_notification(self, message:str=None , icon:str=None):
        """
        position -> left right

        Icon availble selction, default is SP_MessageBoxInformation

        "SP_TitleBarMenuButton",
        "SP_TitleBarMinButton",
        "SP_TitleBarMaxButton",
        "SP_TitleBarCloseButton",
        "SP_MessageBoxInformation",
        "SP_MessageBoxWarning",
        "SP_MessageBoxCritical",
        "SP_MessageBoxQuestion",
        "SP_ArrowUp",
        "SP_ArrowDown",
        "SP_ArrowLeft",
        "SP_ArrowRight",
        "SP_DirHomeIcon",
        "SP_DirIcon",
        "SP_FileIcon",
        "SP_TrashIcon",
        "SP_DriveHDIcon",
        "SP_DriveFDIcon",
        "SP_DriveCDIcon",
        "SP_ComputerIcon",
        "SP_DesktopIcon",
        "SP_DirOpenIcon",
        "SP_BrowserReload",
        "SP_BrowserStop",
    """
        self.source_parent.notification_manager.show_notification(message, icon_new=icon)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = DatabaseConnector()
    window = AdvancePage(db)
    window.show()
    sys.exit(app.exec())
