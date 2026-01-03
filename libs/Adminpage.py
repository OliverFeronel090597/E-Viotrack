from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from libs import GlobalVariable


class AdminPage(QWidget):
    """Reusable login widget with automatic replacement after successful login."""
    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.main_layout)

        # Show login or post-login content depending on user state
        if not getattr(GlobalVariable, "user_login_type", None):
            self.initLoginUI()
        else:
            self.showContent()

    # =====================
    # LOGIN FORM
    # =====================
    def initLoginUI(self):
        """Initialize login form UI."""
        self.login_layout = QVBoxLayout()
        self.login_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_layout.setSpacing(10)

        # Username
        self.user_label = QLabel("User:")
        self.user_label.setObjectName("userlogin")
        self.user_input = QLineEdit()
        self.user_input.setObjectName("userlogin")
        self.user_input.setFixedWidth(200)

        # Password
        self.pass_label = QLabel("Password:")
        self.pass_label.setObjectName("userlogin")

        pass_layout = QHBoxLayout()
        pass_layout.setSpacing(0)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setObjectName("passlogin")
        self.pass_input.setFixedWidth(160)  # leave room for show/hide

        # Show/hide password button
        self.show_hide = QPushButton()
        self.show_hide.setIcon(QIcon("img\\Hide.png"))
        self.show_hide.setObjectName("showhide")
        self.show_hide.setCheckable(True)
        self.show_hide.toggled.connect(self.togglePassword)
        self.show_hide.setFixedSize(40, 32)

        pass_layout.addWidget(self.pass_input)
        pass_layout.addWidget(self.show_hide)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("login")
        self.login_btn.setFixedWidth(200)
        self.login_btn.clicked.connect(self.attemptLogin)

        # Add widgets to layout
        self.login_layout.addWidget(self.user_label)
        self.login_layout.addWidget(self.user_input)
        self.login_layout.addWidget(self.pass_label)
        self.login_layout.addLayout(pass_layout)
        self.login_layout.addWidget(self.login_btn)

        self.main_layout.addLayout(self.login_layout)

    def togglePassword(self, checked: bool):
        """Show or hide password text."""
        if checked:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_hide.setIcon(QIcon("img\\Hide.png"))
        else:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_hide.setIcon(QIcon("img\\Show.png"))

    def attemptLogin(self):
        """Verify credentials and replace login form with content if successful."""
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if self.verify_credentials(username, password):
            # Save login globally
            GlobalVariable.user_login_type = username
            # Remove login form
            self.clearLoginUI()
            # Show post-login content
            self.showContent()
        else:
            # Feedback for invalid login
            self.user_input.clear()
            self.pass_input.clear()
            self.user_input.setPlaceholderText("Invalid username or password")

    def verify_credentials(self, username: str, password: str) -> bool:
        """
        Replace with real authentication (DB) logic.
        Dummy check: username='admin', password='1234'
        """
        return username == "admin" and password == "1234"

    # =====================
    # UTILITY TO CLEAR LOGIN
    # =====================
    def clearLoginUI(self):
        """Remove login widgets and layout from the main layout."""
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

    def clearLayout(self, layout):
        """Recursively remove nested layouts and their widgets."""
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
        """Display post-login content."""
        # Clear any leftover login widgets
        if hasattr(self, "login_layout"):
            self.clearLoginUI()

        self.content_label = QLabel(f"Welcome, {GlobalVariable.user_login_type}")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setStyleSheet("font-size: 20px; font-weight: bold; color: black;")

        # Stretch for vertical centering
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.content_label)
        self.main_layout.addStretch(2)
