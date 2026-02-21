from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QPushButton, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QTimer
from libs.DatabaseConnector import DatabaseConnector
from libs.TablePrint import print_table
from libs.GlobalVariable import is_admin
from libs.EditViolationTypeDialog import EditViolationTypeDialog
from libs import GlobalVariable


class ViolationTypeTableWidget(QWidget):
    def __init__(self, db: DatabaseConnector, parent=None):
        super().__init__(parent)
        self.db = db
        self.advance_parent = parent
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
        print_table(self.all_types)
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
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        dlg = EditViolationTypeDialog(self.db, None, self)
        if dlg.exec():
            self.load_types()

    def edit_type(self, row, col):
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        vtype_id = int(self.table.item(row, 0).text())
        vtype_data = self.db.get_violation_type(vtype_id)
        if vtype_data:
            dlg = EditViolationTypeDialog(self.db, vtype_data, self)
            if dlg.exec():
                self.load_types()

    def delete_type(self):
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            vtype_id = int(self.table.item(row, 0).text())
            vtype = str(self.table.item(row, 1).text())
            confirm = QMessageBox.question(self, "Delete?", f"Delete Violation Type {vtype}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.db.delete_violation_type(vtype_id)
                self.load_types()
                print(f"${GlobalVariable.user_login} Delete violation type {vtype}")

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
