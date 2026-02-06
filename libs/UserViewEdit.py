import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QLabel, QPushButton, QComboBox, QMessageBox, QMenu,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QIcon, QKeyEvent

# Safe import
try:
    from libs.DatabaseConnector import DatabaseConnector
except ImportError:
    from DatabaseConnector import DatabaseConnector

USER_TYPES = ["ADMIN", "OPERATOR"]

# ==========================
# EDIT USER DIALOG
# ==========================

class AutoCapLineEdit(QLineEdit):
    """QLineEdit that auto-capitalizes each word live while typing."""
    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        # Ignore control keys
        if event.text() and not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            cursor_pos = self.cursorPosition()
            text = self.text()

            # Capitalize each word, preserve spaces
            capitalized = " ".join(word.capitalize() if word.strip() else word
                                   for word in text.split(" "))

            if capitalized != text:
                self.blockSignals(True)
                self.setText(capitalized)
                self.blockSignals(False)
                self.setCursorPosition(cursor_pos)


class EditUserDialog(QDialog):
    def __init__(self, db: DatabaseConnector, user_data: dict = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_data = user_data or {}
        self.setWindowTitle("Edit User" if user_data else "New User")
        self.setObjectName("editUserDialog")
        self.setMinimumWidth(350)

        layout = QVBoxLayout()

        # Full Name
        layout.addWidget(QLabel("Full Name", objectName="labelFullName"))
        self.full_name_input = AutoCapLineEdit()
        self.full_name_input.setObjectName("fullNameInput")
        self.full_name_input.setText(self.user_data.get("full_name", ""))
        layout.addWidget(self.full_name_input)

        # User Name
        layout.addWidget(QLabel("User Name", objectName="labelUserName"))
        self.user_name_input = QLineEdit()
        self.user_name_input.setObjectName("userNameInput")
        self.user_name_input.setText(self.user_data.get("user_name", ""))
        self.user_name_input.setReadOnly(bool(self.user_data))
        layout.addWidget(self.user_name_input)

        # Password
        layout.addWidget(QLabel("Password", objectName="labelPassword"))
        pwd_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setObjectName("passwordInput")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_layout.addWidget(self.password_input)

        self.show_pwd_btn = QPushButton()
        self.show_pwd_btn.setObjectName("showHideBtn")
        self.show_pwd_btn.setIcon(QIcon("img\\Hide.png"))
        self.show_pwd_btn.setCheckable(True)
        self.show_pwd_btn.toggled.connect(self.toggle_password)
        pwd_layout.addWidget(self.show_pwd_btn)
        layout.addLayout(pwd_layout)

        # Confirm Password
        layout.addWidget(QLabel("Confirm Password", objectName="labelConfirmPassword"))
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setObjectName("confirmPasswordInput")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_password_input)

        # User Type
        layout.addWidget(QLabel("User Type", objectName="labelUserType"))
        self.user_type_dropdown = QComboBox()
        self.user_type_dropdown.setObjectName("userTypeDropdown")
        self.user_type_dropdown.addItems(USER_TYPES)
        if self.user_data.get("user_type"):
            idx = USER_TYPES.index(self.user_data["user_type"])
            self.user_type_dropdown.setCurrentIndex(idx)
        layout.addWidget(self.user_type_dropdown)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.clicked.connect(self.save_user)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def toggle_password(self, checked):
        """Show/hide password field."""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_pwd_btn.setIcon(QIcon("img\\Show.png"))
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_pwd_btn.setIcon(QIcon("img\\Hide.png"))

    def save_user(self):
        """Validate and save the user to the database."""
        full_name = self.full_name_input.text().strip()
        user_name = self.user_name_input.text().strip()
        password = self.password_input.text().strip() or None
        confirm_password = self.confirm_password_input.text().strip() or None
        user_type = self.user_type_dropdown.currentText()

        if not full_name or not user_name or not user_type:
            QMessageBox.warning(self, "Error", "Full Name, User Name, and User Type are required.")
            return

        if password and password != confirm_password:
            QMessageBox.warning(self, "Error", "Password and Confirm Password do not match.")
            return

        if self.user_data:
            # Update existing user
            self.db.update_system_user(
                user_name,
                full_name=full_name,
                password=password,
                user_type=user_type
            )
        else:
            # New user requires password
            if not password:
                QMessageBox.warning(self, "Error", "Password is required for new user.")
                return
            self.db.add_system_user(full_name, user_name, password, user_type)

        self.accept()


# ==========================
# USER TABLE WITH SEARCH / ADD / DELETE / RIGHT-CLICK
# ==========================
class UserTableWidget(QWidget):
    def __init__(self, db: DatabaseConnector, parent=None):
        super().__init__()
        self.db = db
        self.setWindowTitle("System Users")
        self.setObjectName("userTableWidget")
        self.resize(750, 450)

        layout = QVBoxLayout()

        # --- Top buttons + search ---
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search by Full Name or User Name...")
        self.search_input.textChanged.connect(self.filter_users)
        top_layout.addWidget(QLabel("Search:", objectName="labelSearch"))
        top_layout.addWidget(self.search_input)

        self.add_btn = QPushButton("Add User")
        self.add_btn.setObjectName("addBtn")
        self.add_btn.clicked.connect(self.add_user)
        top_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton("Delete User")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.clicked.connect(self.delete_user)
        top_layout.addWidget(self.delete_btn)

        layout.addLayout(top_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setObjectName("userTable")
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

    # --- Load / Display ---
    def load_users(self):
        self.all_users = self.db.list_system_users()
        self.display_users(self.all_users)

    def display_users(self, users):
        self.table.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            self.table.setItem(row_idx, 0, QTableWidgetItem(user["full_name"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(user["user_name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(user["user_type"]))
        self.table.resizeColumnsToContents()

    # --- Search Filter ---
    def filter_users(self, text):
        text = text.lower().strip()
        filtered = [
            user for user in self.all_users
            if text in user["full_name"].lower() or text in user["user_name"].lower()
        ]
        self.display_users(filtered)

    # --- Add / Edit / Delete ---
    def edit_user(self, row, column):
        user_name_item = self.table.item(row, 1)
        if not user_name_item:
            return
        user_name = user_name_item.text()
        user_data = self.db.get_system_user(user_name)
        if not user_data:
            QMessageBox.warning(self, "Error", "User data not found.")
            return

        dlg = EditUserDialog(self.db, user_data, self)
        if dlg.exec():
            self.load_users()

    def add_user(self):
        dlg = EditUserDialog(self.db, None, self)
        if dlg.exec():
            self.load_users()

    def delete_user(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Select a user to delete.")
            return
        row = selected_items[0].row()
        user_name = self.table.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete user '{user_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_system_user(user_name)
            self.load_users()

    # --- Right-click Context Menu ---
    def show_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item:
            return
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
# APP ENTRY
# ==========================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ==========================
    # QSS THEME
    # ==========================
  

    db = DatabaseConnector()
    window = UserTableWidget(db)
    window.show()
    sys.exit(app.exec())
