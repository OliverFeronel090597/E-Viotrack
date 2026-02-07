from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from libs import GlobalVariable
from libs.DatabaseConnector import DatabaseConnector

# NOTE: Import your combined user/driver widget here
# It must not be instantiated until login
from libs.UserDriverEditView import UserDriver
from libs import GlobalVariable

class AdminPage(QWidget):
    """Admin page with login, post-login content, and logout."""

    def __init__(self, db: DatabaseConnector, login_type: QLabel):
        super().__init__()
        self.db = db
        self.login_type = login_type

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Only create login UI initially
        if not getattr(GlobalVariable, "user_login_type", None):
            self.initLoginUI()
        else:
            self.showContent()  # Already logged in (rare case)

    # =====================
    # LOGIN FORM
    # =====================
    def initLoginUI(self):
        self.login_layout = QVBoxLayout()
        self.login_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_layout.setSpacing(10)

        # Username
        self.user_label = QLabel("User:")
        self.user_label.setObjectName("passlogin")
        self.user_input = QLineEdit()
        self.user_input.setObjectName("userlogin")
        self.user_input.setFixedWidth(200)

        pass_layout = QHBoxLayout()
        pass_layout.setSpacing(0)
        # Password
        self.pass_label = QLabel("Password:")
        self.pass_label.setObjectName("passlogin")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setObjectName("passlogin")
        self.pass_input.setFixedWidth(160)

        self.show_hide = QPushButton()
        self.show_hide.setIcon(QIcon("img\\Hide.png"))
        self.show_hide.setObjectName("showhide")
        self.show_hide.setCheckable(True)
        self.show_hide.toggled.connect(self.togglePassword)
        self.show_hide.setFixedSize(40, 36)

        pass_layout.addWidget(self.pass_input)
        pass_layout.addWidget(self.show_hide)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("login")
        self.login_btn.setFixedWidth(200)
        self.login_btn.clicked.connect(self.attemptLogin)

        # Error label
        self.login_error = QLabel()
        self.login_error.setObjectName("login_error")

        # Add widgets to layout
        self.login_layout.addWidget(self.user_label)
        self.login_layout.addWidget(self.user_input)
        self.login_layout.addWidget(self.pass_label)
        self.login_layout.addLayout(pass_layout)
        self.login_layout.addWidget(self.login_btn)
        self.login_layout.addWidget(self.login_error)

        self.main_layout.addLayout(self.login_layout)

    def togglePassword(self, checked: bool):
        if checked:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_hide.setIcon(QIcon("img\\Show.png"))
        else:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_hide.setIcon(QIcon("img\\Hide.png"))

    # =====================
    # LOGIN AUTHENTICATION
    # =====================
    def attemptLogin(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if not username:
            self.login_error.setText("Username required")
            return
        if not password:
            self.login_error.setText("Password required")
            return

        if self.db.authenticate_user(username, password):
            GlobalVariable.user_login_type = username
            user_type = self.db.get_system_user(username)
            self.login_type.setText(f"USER: {username.upper()} {user_type['user_type']}")
            GlobalVariable.user_login_type = user_type['user_type']
            self.clearLoginUI()
            self.showContent()
        else:
            self.pass_input.clear()
            self.login_error.setText("Invalid username or password")

    # =====================
    # CLEAR LOGIN UI
    # =====================
    def clearLoginUI(self):
        if hasattr(self, "login_layout"):
            while self.login_layout.count():
                item = self.login_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                elif item.layout():
                    self.clearLayout(item.layout())
            self.main_layout.removeItem(self.login_layout)
            self.login_layout.setParent(None)
            del self.login_layout

    def clearLayout(self, layout: QHBoxLayout | QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self.clearLayout(item.layout())
        layout.setParent(None)

    # =====================
    # POST-LOGIN CONTENT
    # =====================
    def showContent(self):
        # Logout button
        logout_layout = QHBoxLayout()
        logout_layout.addStretch()
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.logout)
        logout_layout.addWidget(self.logout_btn)
        self.main_layout.addLayout(logout_layout)

        # Instantiate UserDriver only after login
        if not hasattr(self, "user_edit"):
            self.user_edit = UserDriver(self.db, self)

        # Add user/driver table to main layout
        self.main_layout.addWidget(self.user_edit)

    # =====================
    # LOGOUT
    # =====================
    def logout(self):
        # Clear login type
        GlobalVariable.user_login_type = None
        self.login_type.setText("USER:")

        # Remove user table and logout button
        if hasattr(self, "user_edit"):
            self.main_layout.removeWidget(self.user_edit)
            self.user_edit.setParent(None)
            del self.user_edit

        if hasattr(self, "logout_btn"):
            self.logout_btn.setParent(None)
            del self.logout_btn

        # Show login UI again
        self.initLoginUI()
