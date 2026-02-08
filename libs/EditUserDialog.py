from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox, QMessageBox
)
try:
    from libs.DatabaseConnector import DatabaseConnector
    from libs.AutoCapital import AutoCapLineEdit
except ImportError:
    from DatabaseConnector import DatabaseConnector
    from AutoCapital import AutoCapLineEdit

USER_TYPES = ["ADMIN", "OPERATOR"]


class EditUserDialog(QDialog):
    def __init__(self, db: DatabaseConnector, user_data=None, parent=None):
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
