from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QPushButton, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QTimer
try:
    from libs.DatabaseConnector import DatabaseConnector
except ImportError:
    from DatabaseConnector import DatabaseConnector

from libs.EditDriverDialog import EditDriverDialog
from libs.GlobalVariable import is_admin


class DriverTableWidget(QWidget):
    def __init__(self, db: DatabaseConnector, parent=None):
        super().__init__(parent)
        self.db = db
        self.advance_parent = parent
        layout = QVBoxLayout()
        layout.setSpacing(8)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Driver ID / Name / Vehicle...")
        self.search_input.textChanged.connect(self.filter_drivers)
        top_layout.addWidget(QLabel("Search:"))
        top_layout.addWidget(self.search_input)
        self.add_btn = QPushButton("Add Driver")
        self.add_btn.clicked.connect(self.add_driver)
        top_layout.addWidget(self.add_btn)
        self.delete_btn = QPushButton("Delete Driver")
        self.delete_btn.clicked.connect(self.delete_driver)
        top_layout.addWidget(self.delete_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Driver ID", "RFID Serial", "Full Name", "Created At", "Vehicle"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellDoubleClicked.connect(self.edit_driver)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.display_drivers()
        self.table.horizontalHeader().setStretchLastSection(True)

    def display_drivers(self, drivers=None):
        # If no filtered list provided → load fresh list
        if drivers is None:
            self.all_drivers = self.db.load_drivers() or []
            drivers = self.all_drivers

        self.table.clearContents()
        self.table.setRowCount(len(drivers))

        for r, d in enumerate(drivers):
            for c, val in enumerate(d):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

        QTimer.singleShot(100, lambda: self.table.resizeColumnsToContents())

    def filter_drivers(self, text):
        text = text.lower().strip()
        filtered = [d for d in self.all_drivers if text in " ".join(str(i).lower() for i in d)]
        self.display_drivers(filtered)

    def add_driver(self):
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        dlg = EditDriverDialog(self.db, None, self)
        if dlg.exec():
            self.display_drivers()

    def edit_driver(self, row, col):
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        driver_id = self.table.item(row, 0).text()
        print(driver_id)
        driver_data = self.db.select_driver(driver_id)
        if driver_data:
            dlg = EditDriverDialog(self.db, {"driver_id": driver_data[0], "rfid_serial": driver_data[1],
                                             "full_name": driver_data[2], "vehicle": driver_data[3]}, self)
            if dlg.exec():
                self.display_drivers()

    def delete_driver(self):
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            driver_id = self.table.item(row, 0).text()
            driver_name = self.table.item(row, 2).text()
            confirm = QMessageBox.question(self, "Delete?", f"Delete driver {driver_name} ID {driver_id}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                print(driver_id)
                self.db.delete_driver(driver_id)
                self.display_drivers()

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item:
            row = item.row()
            menu = QMenu(self)
            edit_action = menu.addAction("Edit Driver")
            delete_action = menu.addAction("Delete Driver")
            action = menu.exec(self.table.mapToGlobal(pos))
            if action == edit_action:
                self.edit_driver(row, 0)
            elif action == delete_action:
                self.table.selectRow(row)
                self.delete_driver()
