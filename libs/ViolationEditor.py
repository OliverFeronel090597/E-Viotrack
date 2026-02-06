import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QLabel, QPushButton, QComboBox, QMessageBox, QMenu,
    QDateEdit, QDoubleSpinBox, QCheckBox, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QKeyEvent

# Safe import
try:
    from libs.DatabaseConnector import DatabaseConnector
except ImportError:
    from DatabaseConnector import DatabaseConnector

USER_TYPES = ["ADMIN", "OPERATOR"]

# ==========================
# AUTO-CAPITALIZE LINEEDIT
# ==========================
class AutoCapLineEdit(QLineEdit):
    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        if event.text() and not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            cursor_pos = self.cursorPosition()
            text = self.text()
            capitalized = " ".join(word.capitalize() if word.strip() else word for word in text.split(" "))
            if capitalized != text:
                self.blockSignals(True)
                self.setText(capitalized)
                self.blockSignals(False)
                self.setCursorPosition(cursor_pos)

# ==========================
# VIOLATION TYPE DIALOG
# ==========================
class EditViolationTypeDialog(QDialog):
    def __init__(self, db: DatabaseConnector, violation_type_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.violation_type_data = violation_type_data or {}
        self.setWindowTitle("Edit Violation Type" if violation_type_data else "New Violation Type")
        self.setMinimumWidth(350)
        layout = QVBoxLayout()
        layout.setSpacing(6)

        layout.addWidget(QLabel("Violation Type"))
        self.type_input = AutoCapLineEdit()
        self.type_input.setText(self.violation_type_data.get("violation_type", ""))
        layout.addWidget(self.type_input)

        layout.addWidget(QLabel("Amount"))
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMinimum(0)
        self.amount_input.setMaximum(1000000)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("$ ")
        if "amount" in self.violation_type_data:
            self.amount_input.setValue(float(self.violation_type_data["amount"]))
        layout.addWidget(self.amount_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_violation_type)
        btn_layout.addWidget(self.save_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_violation_type(self):
        violation_type = self.type_input.text().strip()
        amount = self.amount_input.value()

        if not violation_type:
            QMessageBox.warning(self, "Error", "Violation type is required")
            return
        if amount <= 0:
            QMessageBox.warning(self, "Error", "Amount must be greater than 0")
            return

        if self.violation_type_data:
            # Update existing
            violation_id = self.violation_type_data.get("id")
            if violation_id:
                self.db.update_violation_type(violation_id, violation_type=violation_type, amount=amount)
        else:
            # Add new
            self.db.add_violation_type(violation_type, amount)
        
        self.accept()

# ==========================
# VIOLATION TYPE TABLE
# ==========================
class ViolationTypeTableWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout()
        layout.setSpacing(8)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search violation type...")
        self.search_input.textChanged.connect(self.filter_violation_types)
        top_layout.addWidget(QLabel("Search:"))
        top_layout.addWidget(self.search_input)
        self.add_btn = QPushButton("Add Violation Type")
        self.add_btn.clicked.connect(self.add_violation_type)
        top_layout.addWidget(self.add_btn)
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_violation_type)
        top_layout.addWidget(self.delete_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Violation Type", "Amount"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellDoubleClicked.connect(self.edit_violation_type)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_violation_types()
        self.table.horizontalHeader().setStretchLastSection(True)

    def load_violation_types(self):
        self.all_violation_types = self.db.list_violation_types()
        self.display_violation_types(self.all_violation_types)

    def display_violation_types(self, violation_types):
        self.table.setRowCount(len(violation_types))
        for r, vt in enumerate(violation_types):
            self.table.setItem(r, 0, QTableWidgetItem(str(vt["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(vt["violation_type"]))
            self.table.setItem(r, 2, QTableWidgetItem(f"${vt['amount']:.2f}"))
        self.table.resizeColumnsToContents()

    def filter_violation_types(self, text):
        text = text.lower().strip()
        filtered = [vt for vt in self.all_violation_types if text in vt["violation_type"].lower()]
        self.display_violation_types(filtered)

    def add_violation_type(self):
        dlg = EditViolationTypeDialog(self.db, None, self)
        if dlg.exec():
            self.load_violation_types()

    def edit_violation_type(self, row, col):
        violation_type_id = int(self.table.item(row, 0).text())
        violation_type_data = self.db.get_violation_type(violation_type_id)
        if violation_type_data:
            dlg = EditViolationTypeDialog(self.db, violation_type_data, self)
            if dlg.exec():
                self.load_violation_types()

    def delete_violation_type(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            violation_type_id = int(self.table.item(row, 0).text())
            violation_type = self.table.item(row, 1).text()
            
            confirm = QMessageBox.question(
                self, "Delete?", 
                f"Delete violation type '{violation_type}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                self.db.delete_violation_type(violation_type_id)
                self.load_violation_types()

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item:
            row = item.row()
            menu = QMenu(self)
            edit_action = menu.addAction("Edit Violation Type")
            delete_action = menu.addAction("Delete Violation Type")
            action = menu.exec(self.table.mapToGlobal(pos))
            if action == edit_action:
                self.edit_violation_type(row, 0)
            elif action == delete_action:
                self.table.selectRow(row)
                self.delete_violation_type()

# ==========================
# VIOLATION DIALOG
# ==========================
class EditViolationDialog(QDialog):
    def __init__(self, db: DatabaseConnector, violation_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.violation_data = violation_data or {}
        self.setWindowTitle("Edit Violation" if violation_data else "New Violation")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        layout.setSpacing(6)

        # Get lists for dropdowns
        self.drivers = self.db.execute_query(
            "SELECT driver_id, full_name, vehicle FROM drivers",
            fetch_all=True
        ) or []
        
        self.violation_types = self.db.list_violation_types()
        self.system_users = self.db.list_system_users()

        # Driver selection
        layout.addWidget(QLabel("Driver"))
        self.driver_combo = QComboBox()
        self.driver_combo.addItem("Select Driver", None)
        for driver in self.drivers:
            display_text = f"{driver[1]} ({driver[0]}) - {driver[2]}"
            self.driver_combo.addItem(display_text, driver[0])
        layout.addWidget(self.driver_combo)

        # Violation type selection
        layout.addWidget(QLabel("Violation Type"))
        self.violation_combo = QComboBox()
        self.violation_combo.addItem("Select Violation Type", None)
        for vt in self.violation_types:
            display_text = f"{vt['violation_type']} - ${vt['amount']:.2f}"
            self.violation_combo.addItem(display_text, vt['violation_type'])
        layout.addWidget(self.violation_combo)

        # User (issuer)
        layout.addWidget(QLabel("Issued By"))
        self.user_combo = QComboBox()
        self.user_combo.addItem("Select User", None)
        for user in self.system_users:
            display_text = f"{user['full_name']} ({user['user_type']})"
            self.user_combo.addItem(display_text, user['user_name'])
        layout.addWidget(self.user_combo)

        # Date of violation
        layout.addWidget(QLabel("Violation Date"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        layout.addWidget(self.date_input)

        # Due date
        layout.addWidget(QLabel("Due Date"))
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addDays(30))
        layout.addWidget(self.due_date_input)

        # Amount (auto-filled from violation type, but editable)
        layout.addWidget(QLabel("Amount"))
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMinimum(0)
        self.amount_input.setMaximum(1000000)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("$ ")
        layout.addWidget(self.amount_input)

        # Paid status
        layout.addWidget(QLabel("Payment Status"))
        self.paid_checkbox = QCheckBox("Paid")
        layout.addWidget(self.paid_checkbox)

        # Connect signals
        self.violation_combo.currentIndexChanged.connect(self.update_amount)

        # Pre-fill if editing
        if self.violation_data:
            self.prefill_data()

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_violation)
        btn_layout.addWidget(self.save_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def prefill_data(self):
        """Pre-fill form with existing violation data"""
        # Find driver in combo
        driver_id = self.violation_data.get("driver_id")
        for i in range(self.driver_combo.count()):
            if self.driver_combo.itemData(i) == driver_id:
                self.driver_combo.setCurrentIndex(i)
                break

        # Find violation type in combo
        violation_type = self.violation_data.get("violation")
        for i in range(self.violation_combo.count()):
            if self.violation_combo.itemData(i) == violation_type:
                self.violation_combo.setCurrentIndex(i)
                break

        # Find user in combo
        user_name = self.violation_data.get("user")
        for i in range(self.user_combo.count()):
            if self.user_combo.itemData(i) == user_name:
                self.user_combo.setCurrentIndex(i)
                break

        # Set dates
        if "date" in self.violation_data:
            self.date_input.setDate(QDate.fromString(self.violation_data["date"], "yyyy-MM-dd"))
        if "due_date" in self.violation_data:
            self.due_date_input.setDate(QDate.fromString(self.violation_data["due_date"], "yyyy-MM-dd"))

        # Set amount and paid status
        if "amount" in self.violation_data:
            self.amount_input.setValue(float(self.violation_data["amount"]))
        if "paid" in self.violation_data:
            self.paid_checkbox.setChecked(bool(self.violation_data["paid"]))

    def update_amount(self):
        """Update amount based on selected violation type"""
        violation_type = self.violation_combo.currentData()
        if violation_type:
            for vt in self.violation_types:
                if vt['violation_type'] == violation_type:
                    self.amount_input.setValue(vt['amount'])
                    break

    def save_violation(self):
        # Get selected driver
        driver_id = self.driver_combo.currentData()
        if not driver_id:
            QMessageBox.warning(self, "Error", "Please select a driver")
            return

        # Get driver details
        driver = None
        for d in self.drivers:
            if d[0] == driver_id:
                driver = d
                break
        
        if not driver:
            QMessageBox.warning(self, "Error", "Selected driver not found")
            return

        # Get violation type
        violation_type = self.violation_combo.currentData()
        if not violation_type:
            QMessageBox.warning(self, "Error", "Please select a violation type")
            return

        # Get user
        user_name = self.user_combo.currentData()
        if not user_name:
            QMessageBox.warning(self, "Error", "Please select the issuing user")
            return

        # Get other data
        date = self.date_input.date().toString("yyyy-MM-dd")
        due_date = self.due_date_input.date().toString("yyyy-MM-dd")
        amount = self.amount_input.value()
        paid = 1 if self.paid_checkbox.isChecked() else 0

        # Get driver's RFID (you might need to query this)
        driver_details = self.db.execute_query(
            "SELECT rfid_serial FROM drivers WHERE driver_id=?",
            (driver_id,),
            fetch_one=True
        )
        rfid_serial = driver_details[0] if driver_details else ""

        if self.violation_data:
            # Update existing violation
            violation_id = self.violation_data.get("id")
            if violation_id:
                self.db.update_violation(
                    violation_id,
                    user=user_name,
                    violation=violation_type,
                    paid=paid,
                    due_date=due_date
                )
        else:
            # Add new violation
            self.db.add_violation(
                user=user_name,
                driver_name=driver[1],
                driver_id=driver_id,
                rfid_serial=rfid_serial,
                violation=violation_type,
                vehicle=driver[2],
                date=date,
                due_date=due_date,
                paid=paid
            )
        
        self.accept()

# ==========================
# VIOLATION TABLE
# ==========================
class ViolationTableWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout()
        layout.setSpacing(8)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search driver/violation/vehicle...")
        self.search_input.textChanged.connect(self.filter_violations)
        top_layout.addWidget(QLabel("Search:"))
        top_layout.addWidget(self.search_input)
        self.add_btn = QPushButton("Add Violation")
        self.add_btn.clicked.connect(self.add_violation)
        top_layout.addWidget(self.add_btn)
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_violation)
        top_layout.addWidget(self.delete_btn)
        layout.addLayout(top_layout)

        # Filter by payment status
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Payment Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("All", None)
        self.status_combo.addItem("Unpaid", 0)
        self.status_combo.addItem("Paid", 1)
        self.status_combo.currentIndexChanged.connect(self.load_violations)
        filter_layout.addWidget(self.status_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Driver", "Driver ID", "RFID", "Violation", 
            "Vehicle", "Date", "Due Date", "Amount", "Paid"
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellDoubleClicked.connect(self.edit_violation)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_violations()
        self.table.horizontalHeader().setStretchLastSection(True)

    def load_violations(self):
        status_filter = self.status_combo.currentData()
        if status_filter is not None:
            self.all_violations = self.db.execute_query(
                "SELECT * FROM violations WHERE paid=? ORDER BY date DESC",
                (status_filter,),
                fetch_all=True
            ) or []
        else:
            self.all_violations = self.db.execute_query(
                "SELECT * FROM violations ORDER BY date DESC",
                fetch_all=True
            ) or []
        self.display_violations(self.all_violations)

    def display_violations(self, violations):
        self.table.setRowCount(len(violations))
        for r, v in enumerate(violations):
            for c, val in enumerate(v):
                if c == 9:  # Paid column
                    item = QTableWidgetItem("Yes" if val else "No")
                    item.setForeground(Qt.GlobalColor.green if val else Qt.GlobalColor.red)
                elif c == 8:  # Amount column
                    item = QTableWidgetItem(f"${float(val):.2f}" if val else "$0.00")
                else:
                    item = QTableWidgetItem(str(val))
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

    def filter_violations(self, text):
        text = text.lower().strip()
        filtered = []
        for v in self.all_violations:
            # Search in driver name (index 2), driver ID (3), violation (5), vehicle (6)
            searchable = f"{v[2]} {v[3]} {v[5]} {v[6]}".lower()
            if text in searchable:
                filtered.append(v)
        self.display_violations(filtered)

    def add_violation(self):
        dlg = EditViolationDialog(self.db, None, self)
        if dlg.exec():
            self.load_violations()

    def edit_violation(self, row, col):
        violation_id = int(self.table.item(row, 0).text())
        violation_data = self.db.get_violation(violation_id)
        if violation_data:
            dlg = EditViolationDialog(self.db, violation_data, self)
            if dlg.exec():
                self.load_violations()

    def delete_violation(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            violation_id = int(self.table.item(row, 0).text())
            driver_name = self.table.item(row, 1).text()
            violation_type = self.table.item(row, 4).text()
            
            confirm = QMessageBox.question(
                self, "Delete?", 
                f"Delete violation '{violation_type}' for {driver_name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                self.db.delete_violation(violation_id)
                self.load_violations()

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item:
            row = item.row()
            menu = QMenu(self)
            edit_action = menu.addAction("Edit Violation")
            delete_action = menu.addAction("Delete Violation")
            mark_paid_action = menu.addAction("Mark as Paid")
            mark_unpaid_action = menu.addAction("Mark as Unpaid")
            
            action = menu.exec(self.table.mapToGlobal(pos))
            
            violation_id = int(self.table.item(row, 0).text())
            
            if action == edit_action:
                self.edit_violation(row, 0)
            elif action == delete_action:
                self.table.selectRow(row)
                self.delete_violation()
            elif action == mark_paid_action:
                self.db.update_violation(violation_id, paid=1)
                self.load_violations()
            elif action == mark_unpaid_action:
                self.db.update_violation(violation_id, paid=0)
                self.load_violations()

# ==========================
# USER TABLE (from your code)
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
        self.table.resizeColumnsToContents()

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
# DRIVER TABLE (from your code)
# ==========================
class DriverTableWidget(QWidget):
    def __init__(self, db):
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
        self.load_drivers()
        self.table.horizontalHeader().setStretchLastSection(True)

    def load_drivers(self):
        self.all_drivers = self.db.execute_query(
            "SELECT driver_id, rfid_serial, full_name, created_at, vehicle FROM drivers",
            fetch_all=True
        ) or []
        self.display_drivers(self.all_drivers)

    def display_drivers(self, drivers):
        self.table.setRowCount(len(drivers))
        for r, d in enumerate(drivers):
            for c, val in enumerate(d):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()

    def filter_drivers(self, text):
        text = text.lower().strip()
        filtered = [d for d in self.all_drivers if text in " ".join(str(i).lower() for i in d)]
        self.display_drivers(filtered)

    def add_driver(self):
        dlg = EditDriverDialog(self.db, None, self)
        if dlg.exec():
            self.load_drivers()

    def edit_driver(self, row, col):
        driver_id = self.table.item(row, 0).text()
        driver_data = self.db.execute_query(
            "SELECT driver_id, rfid_serial, full_name, vehicle FROM drivers WHERE driver_id=?",
            (driver_id,), fetch_one=True
        )
        if driver_data:
            dlg = EditDriverDialog(self.db, {"driver_id": driver_data[0], "rfid_serial": driver_data[1],
                                             "full_name": driver_data[2], "vehicle": driver_data[3]}, self)
            if dlg.exec():
                self.load_drivers()

    def delete_driver(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            driver_id = self.table.item(row, 0).text()
            confirm = QMessageBox.question(self, "Delete?", f"Delete driver {driver_id}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.db.execute_query("DELETE FROM drivers WHERE driver_id=?", (driver_id,))
                self.load_drivers()

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
# EDIT USER DIALOG (from your code)
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
# EDIT DRIVER DIALOG (from your code)
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

# ==========================
# MAIN WINDOW SIDE BY SIDE (4 tables)
# ==========================
class AdminPanel(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Admin Panel - All Tables")
        self.resize(1800, 800)
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Create splitter for horizontal arrangement
        splitter_top = QSplitter(Qt.Orientation.Horizontal)
        splitter_bottom = QSplitter(Qt.Orientation.Horizontal)
        
        # Add tables to splitters
        splitter_top.addWidget(UserTableWidget(db))
        splitter_top.addWidget(DriverTableWidget(db))
        splitter_bottom.addWidget(ViolationTypeTableWidget(db))
        splitter_bottom.addWidget(ViolationTableWidget(db))
        
        # Set initial sizes
        splitter_top.setSizes([900, 900])
        splitter_bottom.setSizes([900, 900])
        
        # Add splitters to main layout
        main_layout.addWidget(splitter_top)
        main_layout.addWidget(splitter_bottom)
        
        # Make splitters resizable
        splitter_top.setHandleWidth(8)
        splitter_bottom.setHandleWidth(8)
        
        # Set stretch factors
        main_layout.setStretchFactor(splitter_top, 1)
        main_layout.setStretchFactor(splitter_bottom, 1)
        
        self.setLayout(main_layout)

# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = DatabaseConnector()
    window = AdminPanel(db)
    window.show()
    sys.exit(app.exec())