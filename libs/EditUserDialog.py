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
        self.users = self.db.select_all_user()  # list of tuples with usernames
        self.user_data = user_data or {}
        self.is_edit_mode = bool(user_data)

        self.setWindowTitle("Edit User" if self.is_edit_mode else "New User")
        self.setMinimumWidth(350)

        layout = QVBoxLayout()
        layout.setSpacing(6)

        # --- Full Name ---
        layout.addWidget(QLabel("Full Name"))
        self.full_name_input = AutoCapLineEdit()
        self.full_name_input.setText(self.user_data.get("full_name", ""))
        layout.addWidget(self.full_name_input)

        # --- User Name ---
        layout.addWidget(QLabel("User Name"))
        self.user_name_input = QLineEdit()
        self.user_name_input.setText(self.user_data.get("user_name", ""))
        if self.is_edit_mode:
            self.user_name_input.setReadOnly(True)  # prevent changing username in edit
        layout.addWidget(self.user_name_input)

        # --- Password ---
        layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # --- Confirm Password ---
        layout.addWidget(QLabel("Confirm Password"))
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_password_input)

        # --- User Type ---
        layout.addWidget(QLabel("User Type"))
        self.user_type_dropdown = QComboBox()
        self.user_type_dropdown.addItems(USER_TYPES)
        if self.user_data.get("user_type"):
            idx = USER_TYPES.index(self.user_data["user_type"])
            self.user_type_dropdown.setCurrentIndex(idx)
        layout.addWidget(self.user_type_dropdown)

        # --- Buttons ---
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

        # --- Check required fields ---
        missing_fields = []
        if not full_name:
            missing_fields.append("Full Name")
        if not user_name:
            missing_fields.append("User Name")
        if not user_type:
            missing_fields.append("User Type")
        if not self.is_edit_mode and not password:
            missing_fields.append("Password")  # new user must have password

        if missing_fields:
            QMessageBox.warning(
                self,
                "Missing Fields",
                f"Please fill the following fields: {', '.join(missing_fields)}"
            )
            return

        # --- Password confirmation ---
        if password and password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        # --- Duplicate username check ---
        existing_usernames = [u[0] for u in self.users]  # db returns list of tuples
        if not self.is_edit_mode and user_name in existing_usernames:
            QMessageBox.warning(self, "Error", f"Username '{user_name}' already exists")
            return

        # --- Save to database ---
        try:
            if self.is_edit_mode:
                # Edit mode: update user
                self.db.update_system_user(
                    user_name,
                    full_name=full_name,
                    password=password if password else None,
                    user_type=user_type
                )
            else:
                # Add mode: new user
                self.db.add_system_user(full_name, user_name, password, user_type)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save user: {str(e)}")
            return

        self.accept()
