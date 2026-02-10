from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QPushButton, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QTimer

from libs.EditUserDialog import EditUserDialog
from libs.GlobalVariable import is_admin


class UserTableWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.advance_parent = parent
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
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        dlg = EditUserDialog(self.db, None, self)
        if dlg.exec():
            self.load_users()

    def edit_user(self, row, col):
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        user_name = self.table.item(row, 1).text()
        user_data = self.db.get_system_user(user_name)
        if user_data:
            dlg = EditUserDialog(self.db, user_data, self)
            if dlg.exec():
                self.load_users()

    def delete_user(self):
        if not is_admin():
            self.advance_parent.show_notification("Please Login as Admin To Access this Feature.", icon="SP_MessageBoxWarning")
            return
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            user_name = self.table.item(row, 1).text()
            user_id = self.table.item(row, 2).text()
            print(f"Username {user_name}")
            confirm = QMessageBox.question(self, "Delete?", f"Delete user {user_name.upper()} Type {user_id}?",
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
