from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QPushButton, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QTimer
from libs.DatabaseConnector import DatabaseConnector
from libs.TablePrint import print_table
from libs.GlobalVariable import is_admin
from libs.EditViolationDialog import EditViolationDialog


class ViolationTableWidget(QWidget):
    def __init__(self, db: DatabaseConnector, parent=None):
        super().__init__(parent)
        self.db = db
        self.advance_parent = parent
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
        rows = self.db.get_all_violations()
        self.all_violations = []

        for r in rows:
            # Safe tuple access with default None if tuple is shorter
            v = {
                "id": r[0] if len(r) > 0 else None,
                "user": r[1] if len(r) > 1 else "",
                "driver_name": r[2] if len(r) > 2 else "",
                "driver_id": r[3] if len(r) > 3 else "",
                "rfid_serial": r[4] if len(r) > 4 else "",
                "violation": r[5] if len(r) > 5 else "",
                "vehicle": r[6] if len(r) > 6 else "",
                "issue_date": r[7] if len(r) > 7 else "",
                "amount": r[8] if len(r) > 8 else 0,
                "due_date": r[9] if len(r) > 9 else "",
                "paid": r[10] if len(r) > 10 else "",
            }
            self.all_violations.append(v)

        print_table(self.all_violations)
        self.display_violations(self.all_violations)


    def display_violations(self, violations):
        self.table.setRowCount(len(violations))
        for r, v in enumerate(violations):
            self.table.setItem(r, 0, QTableWidgetItem(str(v.get("driver_name", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(str(v.get("driver_id", ""))))
            self.table.setItem(r, 2, QTableWidgetItem(str(v.get("rfid_serial", ""))))
            self.table.setItem(r, 3, QTableWidgetItem(str(v.get("violation", ""))))
            self.table.setItem(r, 4, QTableWidgetItem(str(v.get("vehicle", ""))))
            self.table.setItem(r, 5, QTableWidgetItem(str(v.get("issue_date", ""))))
            self.table.setItem(r, 6, QTableWidgetItem(str(v.get("amount", 0))))
            self.table.setItem(r, 7, QTableWidgetItem(str(v.get("due_date", ""))))
            self.table.setItem(r, 8, QTableWidgetItem(str(v.get("paid", ""))))

        QTimer.singleShot(10, self.table.resizeColumnsToContents)

    def filter_violations(self, text):
        filtered = [v for v in self.all_violations if text.lower() in v.get("driver_name", "").lower() or text.lower() in v.get("violation", "").lower()]
        self.display_violations(filtered)

    def add_violation(self):
        dlg = EditViolationDialog(self.db, None, self)
        if dlg.exec():
            self.load_violations()

    def edit_violation(self, row, col):
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        violation_data = self.all_violations[row]  # row index corresponds to self.all_violations
        dlg = EditViolationDialog(self.db, violation_data, self)
        if dlg.exec():
            self.load_violations()

    def delete_violation(self):
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            violation_id = str(self.table.item(row, 1).text())
            violator_name = str(self.table.item(row, 0).text())
            confirm = QMessageBox.question(self, "Delete?", f"Delete Violation of {violator_name} ID {violation_id}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.db.delete_violation(violation_id)
                self.load_violations()


    def paid_violation(self):
        # Check admin rights
        if not is_admin():
            self.advance_parent.show_notification(
                "Please Login as Admin To Access this Feature.",
                icon="SP_MessageBoxWarning"
            )
            return

        selected = self.table.selectedItems()
        if not selected:
            self.advance_parent.show_notification(
                "No violation selected.",
                icon="SP_MessageBoxInformation"
            )
            return

        row = selected[0].row()
        violator_name = str(self.table.item(row, 0).text())
        violator_id = str(self.table.item(row, 1).text())
        violation_date = str(self.table.item(row, 5).text())  # optional if you want to filter by date

        # Confirm action
        confirm = QMessageBox.question(
            self,
            "Mark as Paid?",
            f"Mark violation of {violator_name} (ID: {violator_id}) on {violation_date} as paid?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            # Updated DatabaseConnector method accepts date as filter
            self.db.paid_violation(violator_id, violator_name, violation_date)
            self.load_violations()


    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item:
            row = item.row()
            menu = QMenu(self)
            edit_action = menu.addAction("Edit Violation")
            delete_action = menu.addAction("Delete Violation")
            paid_action = menu.addAction("Violation Paid")
            action = menu.exec(self.table.mapToGlobal(pos))
            if action == edit_action:
                self.edit_violation(row, 0)
            elif action == delete_action:
                self.table.selectRow(row)
                self.delete_violation()
            elif action == paid_action:
                self.paid_violation()
