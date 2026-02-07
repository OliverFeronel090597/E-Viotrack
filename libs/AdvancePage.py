import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QLabel, QPushButton, QComboBox, QMessageBox, QMenu, QSplitter
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime

try:
    from libs.DatabaseConnector import DatabaseConnector
except ImportError:
    from DatabaseConnector import DatabaseConnector

# ==========================
# DIALOGS
# ==========================
class EditViolationTypeDialog(QDialog):
    def __init__(self, db: DatabaseConnector, vtype_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.vtype_data = vtype_data or {}
        self.setWindowTitle("Edit Violation Type" if vtype_data else "New Violation Type")
        self.setMinimumWidth(300)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Violation Type"))
        self.type_input = QLineEdit()
        self.type_input.setText(self.vtype_data.get("violation_type", ""))
        layout.addWidget(self.type_input)

        layout.addWidget(QLabel("Amount"))
        self.amount_input = QLineEdit()
        self.amount_input.setText(str(self.vtype_data.get("amount", "")))
        layout.addWidget(self.amount_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save(self):
        vtype = self.type_input.text().strip()
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Amount must be a number")
            return
        if not vtype:
            QMessageBox.warning(self, "Error", "Violation Type required")
            return

        if self.vtype_data:
            self.db.update_violation_type(self.vtype_data["id"], violation_type=vtype, amount=amount)
        else:
            self.db.add_violation_type(vtype, amount)
        self.accept()


class EditViolationDialog(QDialog):
    def __init__(self, db: DatabaseConnector, violation=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.violation = violation or {}
        self.setWindowTitle("Edit Violation" if violation else "New Violation")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Driver ID"))
        self.driver_id_input = QLineEdit()
        self.driver_id_input.setText(str(self.violation.get("driver_id", "")))
        layout.addWidget(self.driver_id_input)

        layout.addWidget(QLabel("Driver Name"))
        self.driver_name_input = QLineEdit()
        self.driver_name_input.setText(str(self.violation.get("driver_name", "")))
        layout.addWidget(self.driver_name_input)

        layout.addWidget(QLabel("RFID Serial"))
        self.rfid_input = QLineEdit()
        self.rfid_input.setText(str(self.violation.get("rfid_serial", "")))
        layout.addWidget(self.rfid_input)

        layout.addWidget(QLabel("Violation Type"))
        self.violation_type_dropdown = QComboBox()
        self.types_list = db.list_violation_types()
        self.violation_type_dropdown.addItems([t["violation_type"] for t in self.types_list])
        if self.violation.get("violation"):
            index = next((i for i, t in enumerate(self.types_list) if t["violation_type"] == self.violation["violation"]), 0)
            self.violation_type_dropdown.setCurrentIndex(index)
        layout.addWidget(self.violation_type_dropdown)

        layout.addWidget(QLabel("Vehicle"))
        self.vehicle_input = QLineEdit()
        self.vehicle_input.setText(str(self.violation.get("vehicle", "")))
        layout.addWidget(self.vehicle_input)

        layout.addWidget(QLabel("Date (YYYY-MM-DD)"))
        self.date_input = QLineEdit()
        self.date_input.setText(str(self.violation.get("date", datetime.now().strftime("%Y-%m-%d"))))
        layout.addWidget(self.date_input)

        layout.addWidget(QLabel("Due Date (YYYY-MM-DD)"))
        self.due_date_input = QLineEdit()
        self.due_date_input.setText(str(self.violation.get("due_date", datetime.now().strftime("%Y-%m-%d"))))
        layout.addWidget(self.due_date_input)

        layout.addWidget(QLabel("Amount"))
        self.amount_input = QLineEdit()
        self.amount_input.setText(str(self.violation.get("amount", 0)))
        self.amount_input.setReadOnly(True)  # amount comes from violation type
        layout.addWidget(self.amount_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Update amount when violation type changes
        self.violation_type_dropdown.currentIndexChanged.connect(self.update_amount)

    def update_amount(self):
        violation = self.violation_type_dropdown.currentText()
        amount = next((t["amount"] for t in self.types_list if t["violation_type"] == violation), 0)
        self.amount_input.setText(str(amount))

    def save(self):
        driver_id = self.driver_id_input.text().strip()
        driver_name = self.driver_name_input.text().strip()
        rfid = self.rfid_input.text().strip()
        violation = self.violation_type_dropdown.currentText()
        vehicle = self.vehicle_input.text().strip()
        date = self.date_input.text().strip()
        due_date = self.due_date_input.text().strip()
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Amount must be a number")
            return

        if not all([driver_id, driver_name, rfid, violation, vehicle, date, due_date]):
            QMessageBox.warning(self, "Error", "All fields required")
            return

        if self.violation:
            # edit
            self.db.update_violation(
                self.violation["id"],
                user="Admin",
                violation=violation,
                paid=self.violation.get("paid", 0),
                due_date=due_date
            )
        else:
            # add
            self.db.add_violation(
                user="Admin",
                driver_name=driver_name,
                driver_id=driver_id,
                rfid_serial=rfid,
                violation=violation,
                vehicle=vehicle,
                date=date,
                amount=amount,
                due_date=due_date,
                paid=0
            )
        self.accept()

# ==========================
# TABLES
# ==========================
class ViolationTypeTableWidget(QWidget):
    def __init__(self, db: DatabaseConnector):
        super().__init__()
        self.db = db
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Violation Type...")
        self.search_input.textChanged.connect(self.filter_types)
        top_layout.addWidget(QLabel("Search:"))
        top_layout.addWidget(self.search_input)

        self.add_btn = QPushButton("Add Type")
        self.add_btn.clicked.connect(self.add_type)
        self.delete_btn = QPushButton("Delete Type")
        self.delete_btn.clicked.connect(self.delete_type)
        top_layout.addWidget(self.add_btn)
        top_layout.addWidget(self.delete_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Violation Type", "Amount"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellDoubleClicked.connect(self.edit_type)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.load_types()
        self.table.horizontalHeader().setStretchLastSection(True)

    def load_types(self):
        self.all_types = self.db.list_violation_types()
        self.display_types(self.all_types)

    def display_types(self, types):
        self.table.setRowCount(len(types))
        for r, t in enumerate(types):
            self.table.setItem(r, 0, QTableWidgetItem(str(t["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(t["violation_type"]))
            self.table.setItem(r, 2, QTableWidgetItem(str(t["amount"])))
        QTimer.singleShot(100, self.table.resizeColumnsToContents)

    def filter_types(self, text):
        filtered = [t for t in self.all_types if text.lower() in t["violation_type"].lower()]
        self.display_types(filtered)

    def add_type(self):
        dlg = EditViolationTypeDialog(self.db, None, self)
        if dlg.exec():
            self.load_types()

    def edit_type(self, row, col):
        vtype_id = int(self.table.item(row, 0).text())
        vtype_data = self.db.get_violation_type(vtype_id)
        if vtype_data:
            dlg = EditViolationTypeDialog(self.db, vtype_data, self)
            if dlg.exec():
                self.load_types()

    def delete_type(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            vtype_id = int(self.table.item(row, 0).text())
            confirm = QMessageBox.question(self, "Delete?", f"Delete Violation Type ID {vtype_id}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.db.delete_violation_type(vtype_id)
                self.load_types()

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item:
            row = item.row()
            menu = QMenu(self)
            edit_action = menu.addAction("Edit Type")
            delete_action = menu.addAction("Delete Type")
            action = menu.exec(self.table.mapToGlobal(pos))
            if action == edit_action:
                self.edit_type(row, 0)
            elif action == delete_action:
                self.table.selectRow(row)
                self.delete_type()


class ViolationTableWidget(QWidget):
    def __init__(self, db: DatabaseConnector):
        super().__init__()
        self.db = db
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Driver Name / Violation...")
        self.search_input.textChanged.connect(self.filter_violations)
        top_layout.addWidget(QLabel("Search:"))
        top_layout.addWidget(self.search_input)

        self.add_btn = QPushButton("Add Violation")
        self.add_btn.clicked.connect(self.add_violation)
        self.delete_btn = QPushButton("Delete Violation")
        self.delete_btn.clicked.connect(self.delete_violation)
        top_layout.addWidget(self.add_btn)
        top_layout.addWidget(self.delete_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["Driver Name", "Driver ID", "RFID", "Violation",
                                              "Vehicle", "Date", "Amount", "Due Date", "Paid"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellDoubleClicked.connect(self.edit_violation)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.load_violations()
        self.table.horizontalHeader().setStretchLastSection(True)

    def load_violations(self):
        self.all_violations = self.db.list_violations()
        # Fix swapped keys: amount, due_date, paid
        for v in self.all_violations:
            # If due_date is a number, it's actually amount
            if isinstance(v.get("due_date"), (int, float)):
                v["amount"] = v["due_date"]
                v["due_date"] = v.get("paid", "")   # move date string to due_date
                v["paid"] = 0                        # reset paid if missing
            else:
                v.setdefault("amount", 0)
                v.setdefault("due_date", "")
                v.setdefault("paid", 0)
        self.display_violations(self.all_violations)

    def display_violations(self, violations):
        self.table.setRowCount(len(violations))
        for r, v in enumerate(violations):
            self.table.setItem(r, 0, QTableWidgetItem(str(v.get("driver_name", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(str(v.get("driver_id", ""))))
            self.table.setItem(r, 2, QTableWidgetItem(str(v.get("rfid_serial", ""))))
            self.table.setItem(r, 3, QTableWidgetItem(str(v.get("violation", ""))))
            self.table.setItem(r, 4, QTableWidgetItem(str(v.get("vehicle", ""))))
            self.table.setItem(r, 5, QTableWidgetItem(str(v.get("date", ""))))
            self.table.setItem(r, 6, QTableWidgetItem(str(v.get("amount", 0))))   # amount is float
            self.table.setItem(r, 7, QTableWidgetItem(str(v.get("due_date", ""))))
            self.table.setItem(r, 8, QTableWidgetItem(str(v.get("paid", 0))))
        QTimer.singleShot(100, self.table.resizeColumnsToContents)

    def filter_violations(self, text):
        filtered = [v for v in self.all_violations if text.lower() in v.get("driver_name", "").lower() or text.lower() in v.get("violation", "").lower()]
        self.display_violations(filtered)

    def add_violation(self):
        dlg = EditViolationDialog(self.db, None, self)
        if dlg.exec():
            self.load_violations()

    def edit_violation(self, row, col):
        violation_data = self.all_violations[row]  # row index corresponds to self.all_violations
        dlg = EditViolationDialog(self.db, violation_data, self)
        if dlg.exec():
            self.load_violations()

    def delete_violation(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            violation_id = int(self.table.item(row, 0).text())
            confirm = QMessageBox.question(self, "Delete?", f"Delete Violation ID {violation_id}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
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
            action = menu.exec(self.table.mapToGlobal(pos))
            if action == edit_action:
                self.edit_violation(row, 0)
            elif action == delete_action:
                self.table.selectRow(row)
                self.delete_violation()


# ==========================
# MAIN WINDOW
# ==========================
class AdvancePage(QWidget):
    def __init__(self, db: DatabaseConnector):
        super().__init__()
        self.db = db

        # Use a horizontal splitter instead of a simple layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Add widgets to splitter
        self.violation_table = ViolationTableWidget(db)
        self.violation_type_table = ViolationTypeTableWidget(db)
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = DatabaseConnector()
    window = AdvancePage(db)
    window.show()
    sys.exit(app.exec())
