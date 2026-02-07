import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QLabel, QPushButton, QComboBox, QMessageBox, QMenu, QSplitter
)
from PyQt6.QtCore import Qt, QTimer

# Safe import
try:
    from libs.DatabaseConnector import DatabaseConnector
    from libs.AutoCapital import AutoCapLineEdit
except ImportError:
    from DatabaseConnector import DatabaseConnector
    from AutoCapital import AutoCapLineEdit

USER_TYPES = ["ADMIN", "OPERATOR"]

# ==========================
# EDIT USER DIALOG
# ==========================
class EditUserDialog(QDialog):
    def __init__(self, db:DatabaseConnector, user_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_data = user_data or {}
        self.setWindowTitle("Edit User" if user_data else "New User")
        self.setMinimumWidth(350)
        layout = QVBoxLayout()
        layout.setSpacing(6)

        layout.addWidget(QLabel("Full Name"))
        self.full_name_input = AutoCapLineEdit()
        self.full_name_input.setText(self.user_data.get("full_name", ""))
        layout.addWidget(self.full_name_input)

        layout.addWidget(QLabel("User Name"))
        self.user_name_input = QLineEdit()
        self.user_name_input.setText(self.user_data.get("user_name", ""))
        self.user_name_input.setReadOnly(bool(user_data))
        layout.addWidget(self.user_name_input)

        layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        layout.addWidget(QLabel("Confirm Password"))
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_password_input)

        layout.addWidget(QLabel("User Type"))
        self.user_type_dropdown = QComboBox()
        self.user_type_dropdown.addItems(USER_TYPES)
        if self.user_data.get("user_type"):
            idx = USER_TYPES.index(self.user_data["user_type"])
            self.user_type_dropdown.setCurrentIndex(idx)
        layout.addWidget(self.user_type_dropdown)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_user)
        btn_layout.addWidget(self.save_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_user(self):
        full_name = self.full_name_input.text().strip()
        user_name = self.user_name_input.text().strip()
        password = self.password_input.text().strip() or None
        confirm = self.confirm_password_input.text().strip() or None
        user_type = self.user_type_dropdown.currentText()

        if not full_name or not user_name or not user_type:
            QMessageBox.warning(self, "Error", "Full Name, User Name, and User Type required")
            return
        if password and password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
        if self.user_data:
            self.db.update_system_user(user_name, full_name=full_name, password=password, user_type=user_type)
        else:
            if not password:
                QMessageBox.warning(self, "Error", "Password required for new user")
                return
            self.db.add_system_user(full_name, user_name, password, user_type)
        self.accept()

# ==========================
# USER TABLE
# ==========================
class UserTableWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout()
        layout.setSpacing(8)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Full Name / User Name...")
        self.search_input.textChanged.connect(self.filter_users)
        top_layout.addWidget(QLabel("Search:"))
        top_layout.addWidget(self.search_input)
        self.add_btn = QPushButton("Add User")
        self.add_btn.clicked.connect(self.add_user)
        top_layout.addWidget(self.add_btn)
        self.delete_btn = QPushButton("Delete User")
        self.delete_btn.clicked.connect(self.delete_user)
        top_layout.addWidget(self.delete_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Full Name", "User Name", "User Type"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellDoubleClicked.connect(self.edit_user)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_users()
        self.table.horizontalHeader().setStretchLastSection(True)

    def load_users(self):
        self.all_users = self.db.list_system_users()
        self.display_users(self.all_users)

    def display_users(self, users):
        self.table.setRowCount(len(users))
        for r, u in enumerate(users):
            self.table.setItem(r, 0, QTableWidgetItem(u["full_name"]))
            self.table.setItem(r, 1, QTableWidgetItem(u["user_name"]))
            self.table.setItem(r, 2, QTableWidgetItem(u["user_type"]))
        QTimer.singleShot(100, self.table.resizeColumnsToContents)


    def filter_users(self, text):
        text = text.lower().strip()
        filtered = [u for u in self.all_users if text in u["full_name"].lower() or text in u["user_name"].lower()]
        self.display_users(filtered)

    def add_user(self):
        dlg = EditUserDialog(self.db, None, self)
        if dlg.exec():
            self.load_users()

    def edit_user(self, row, col):
        user_name = self.table.item(row, 1).text()
        user_data = self.db.get_system_user(user_name)
        if user_data:
            dlg = EditUserDialog(self.db, user_data, self)
            if dlg.exec():
                self.load_users()

    def delete_user(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            user_name = self.table.item(row, 1).text()
            confirm = QMessageBox.question(self, "Delete?", f"Delete user {user_name}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.db.delete_system_user(user_name)
                self.load_users()

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item:
            row = item.row()
            menu = QMenu(self)
            edit_action = menu.addAction("Edit User")
            delete_action = menu.addAction("Delete User")
            action = menu.exec(self.table.mapToGlobal(pos))
            if action == edit_action:
                self.edit_user(row, 0)
            elif action == delete_action:
                self.table.selectRow(row)
                self.delete_user()

# ==========================
# DRIVER TABLE
# ==========================
class EditDriverDialog(QDialog):
    def __init__(self, db, driver_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.driver_data = driver_data or {}
        self.setWindowTitle("Edit Driver" if driver_data else "New Driver")
        self.setMinimumWidth(350)
        layout = QVBoxLayout()
        layout.setSpacing(6)

        layout.addWidget(QLabel("Driver ID"))
        self.driver_id_input = QLineEdit()
        self.driver_id_input.setText(self.driver_data.get("driver_id", ""))
        self.driver_id_input.setReadOnly(bool(driver_data))
        layout.addWidget(self.driver_id_input)

        layout.addWidget(QLabel("RFID Serial"))
        self.rfid_input = QLineEdit()
        self.rfid_input.setText(self.driver_data.get("rfid_serial", ""))
        layout.addWidget(self.rfid_input)

        layout.addWidget(QLabel("Full Name"))
        self.full_name_input = AutoCapLineEdit()
        self.full_name_input.setText(self.driver_data.get("full_name", ""))
        layout.addWidget(self.full_name_input)

        layout.addWidget(QLabel("Vehicle"))
        self.vehicle_input = QLineEdit()
        self.vehicle_input.setText(self.driver_data.get("vehicle", ""))
        layout.addWidget(self.vehicle_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_driver)
        btn_layout.addWidget(self.save_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_driver(self):
        driver_id = self.driver_id_input.text().strip()
        rfid = self.rfid_input.text().strip()
        name = self.full_name_input.text().strip()
        vehicle = self.vehicle_input.text().strip()
        if not driver_id or not rfid or not name or not vehicle:
            QMessageBox.warning(self, "Error", "All fields required")
            return
        if self.driver_data:
            self.db.update_driver(driver_id, rfid_serial=rfid, full_name=name, vehicle=vehicle)
        else:
            self.db.add_driver(driver_id, rfid, name, vehicle)
        self.accept()

class DriverTableWidget(QWidget):
    def __init__(self, db: DatabaseConnector):
        super().__init__()
        self.db = db
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
        dlg = EditDriverDialog(self.db, None, self)
        if dlg.exec():
            self.display_drivers()

    def edit_driver(self, row, col):
        driver_id = self.table.item(row, 0).text()
        print(driver_id)
        driver_data = self.db.select_driver(driver_id)
        if driver_data:
            dlg = EditDriverDialog(self.db, {"driver_id": driver_data[0], "rfid_serial": driver_data[1],
                                             "full_name": driver_data[2], "vehicle": driver_data[3]}, self)
            if dlg.exec():
                self.display_drivers()

    def delete_driver(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            driver_id = self.table.item(row, 0).text()
            confirm = QMessageBox.question(self, "Delete?", f"Delete driver {driver_id}?",
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

# ==========================
# MAIN WINDOW SIDE BY SIDE
# ==========================
from PyQt6.QtWidgets import QWidget, QSplitter, QHBoxLayout
from PyQt6.QtCore import Qt

class UserDriver(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Admin Panel")
        self.resize(1200, 500)

        # Create a horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Add tables to the splitter
        self.user_table = UserTableWidget(db)
        self.driver_table = DriverTableWidget(db)
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
