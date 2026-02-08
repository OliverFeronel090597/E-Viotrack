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
        rows = self.db.ger_all_violations()
        self.all_violations = []

        for r in rows:
            v = {
                "id": r[0],
                "user": r[1],
                "driver_name": r[2],
                "driver_id": r[3],
                "rfid_serial": r[4],
                "violation": r[5],
                "vehicle": r[6],
                "issue_date": r[7],
                "amount": r[8],
                "due_date": r[9],
                "paid": r[10],
            }

            self.all_violations.append(v)

        print_table(self.all_violations)   # full dict list
        self.display_violations(self.all_violations)


    def display_violations(self, violations):
        self.table.setRowCount(len(violations))
        for r, v in enumerate(violations):
            self.table.setItem(r, 0, QTableWidgetItem(str(v.get("driver_name"   ,""     ))))
            self.table.setItem(r, 1, QTableWidgetItem(str(v.get("driver_id"     ,""     ))))
            self.table.setItem(r, 2, QTableWidgetItem(str(v.get("rfid_serial"   ,""     ))))
            self.table.setItem(r, 3, QTableWidgetItem(str(v.get("violation"     ,""     ))))
            self.table.setItem(r, 4, QTableWidgetItem(str(v.get("vehicle"       ,""     ))))
            self.table.setItem(r, 5, QTableWidgetItem(str(v.get("date"          ,""     ))))
            self.table.setItem(r, 6, QTableWidgetItem(str(v.get("amount"        ,0      ))))
            self.table.setItem(r, 7, QTableWidgetItem(str(v.get("due_date"      ,""     ))))
            self.table.setItem(r, 8, QTableWidgetItem(str(v.get("paid"          ,0      ))))
        QTimer.singleShot(100, self.table.resizeColumnsToContents)

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
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            violation_id = str(self.table.item(row, 1).text())
            violator_name = str(self.table.item(row, 0).text())
            # confirm = QMessageBox.question(self, "Delete?", f"Delete Violation of {violator_name} ID {violation_id}?",
            #                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            # if confirm == QMessageBox.StandardButton.Yes:
            #     self.db.delete_violation(violation_id)
            #     self.load_violations()

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
