from PyQt6.QtWidgets            import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStatusBar, QFrame, QSizePolicy
)
from PyQt6.QtCore               import Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui                import QIcon, QPixmap
import sys


# Absolute path to the folder containing this script,
from libs.Animatedstack         import AnimatedStack
from libs.stylesheetModefier    import StylesheetModifier
from libs.Homepage              import HomePage
from libs.LogPage               import LogPage
from libs.Settings              import RFIDManager
from libs.Adminpage             import AdminPage
from libs.DatabaseConnector     import DatabaseConnector
from libs.Globalenentfilter     import GlobalActivityLogger



# -------------------- MAIN WINDOW --------------------
class E_Viotrack(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("E-Viotrack")
        self.setWindowIcon(QIcon("img/E-VioTrack.png"))
        self.setGeometry(100, 100, 800, 600)

        # CREATE TASKBAR
        self.create_taskbar()

        self.db = DatabaseConnector()
        self.db._create_tables_if_not_exist()

        # NAV STATE
        self.nav_expanded = True
        self.nav_width_expanded = 180
        self.nav_width_collapsed = 75
        self.anim_duration = 250
        self.selected_nav_btn = None
        
        self.icon_size = QSize(40, 40)

        self.styles = StylesheetModifier(
            r"rsc\Styles.qss",
            self
        )
        self.styles.check_file()
        self.styles.save_actual_qss(r"rsc\Styles.qss",)

        # ICON LOADER
        def load_icon(path, size):
            return QIcon(QPixmap(path).scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))

        self.icon_expand = load_icon(
            r"img\LeftPanel.png",
            QSize(32, 32)
        )
        
        self.icon_collapse = load_icon(
            r"img\RightPanel.png",
            QSize(32, 32)
        )

        self.logo_home = QPixmap(
            r"img\Home.png"
        )
        
        self.logo_admin = QPixmap(
            r"img\Admin.png"
        )

        self.logo_logs = QPixmap(
            r"img\History.png"
        )

        self.logo_advance = QPixmap(
            r"img\Advance.png"
        )

        self.logo_settings = QPixmap(
            r"img\Settings.png"
        )

        # ROOT UI
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        self.root_layout = QHBoxLayout(central)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        # NAV BAR
        self.nav_widget = QWidget()
        self.nav_widget.setObjectName("nav")
        self.nav_widget.setMinimumWidth(self.nav_width_expanded)
        self.nav_widget.setMaximumWidth(self.nav_width_expanded)

        nav_layout = QVBoxLayout(self.nav_widget)
        nav_layout.setContentsMargins(6, 6, 6, 6)

        # TOGGLE BUTTON
        toggle_row = QHBoxLayout()
        toggle_row.addStretch()

        self.toggle_btn = QPushButton()
        self.toggle_btn.setFixedSize(44, 44)
        self.toggle_btn.setIcon(self.icon_expand)
        self.toggle_btn.setIconSize(QSize(32, 32))
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_nav)
        self.toggle_btn.setStyleSheet("""
            QPushButton { 
                background: transparent; 
                border: none; }
            QPushButton:hover { 
                background-color: #3b3f45; }
        """)

        toggle_row.addWidget(self.toggle_btn)
        nav_layout.addLayout(toggle_row)

        # NAV BUTTONS
        self.btn_home = QPushButton()
        self.btn_admin = QPushButton()
        self.btn_logs = QPushButton()
        self.btn_advance = QPushButton()
        self.btn_settings = QPushButton()

        # Setup
        self.setup_nav_button(self.btn_home, self.logo_home, "Home")
        nav_layout.addWidget(self.btn_home)
        nav_layout.addWidget(self.create_separator("h"))

        self.setup_nav_button(self.btn_admin, self.logo_admin, "Admin")
        nav_layout.addWidget(self.btn_admin)
        nav_layout.addWidget(self.create_separator("h"))

        self.setup_nav_button(self.btn_logs, self.logo_logs, "Logs")
        nav_layout.addWidget(self.btn_logs)
        nav_layout.addWidget(self.create_separator("h"))

        self.setup_nav_button(self.btn_advance, self.logo_advance, "Advance")
        nav_layout.addWidget(self.btn_advance)
        nav_layout.addWidget(self.create_separator("h"))

        self.setup_nav_button(self.btn_settings, self.logo_settings, "Settings")
        nav_layout.addWidget(self.btn_settings)
        nav_layout.addWidget(self.create_separator("h"))

        nav_layout.addStretch()

        # Fix missing list
        self.nav_buttons = [self.btn_home, self.btn_admin, self.btn_logs, self.btn_advance, self.btn_settings]

        # WIDGETS
        self.home_page = HomePage(self.db)
        self.admin_page = AdminPage(self.db, self.login_type)
        self.log_page = LogPage()
        self.settings_page = RFIDManager(self.home_page, self.db)

        # STACK
        self.stack = AnimatedStack(duration=self.anim_duration)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.admin_page)
        self.stack.addWidget(self.log_page)
        self.stack.addWidget(self.settings_page)

        self.root_layout.addWidget(self.nav_widget)
        self.root_layout.addWidget(self.stack, 1)

        # NAV CLICK HANDLERS
        self.btn_home.clicked.connect(lambda: self.stack.slide_to(0))
        self.btn_admin.clicked.connect(lambda: self.stack.slide_to(1))
        self.btn_logs.clicked.connect(lambda: self.stack.slide_to(2))
        self.btn_settings.clicked.connect(lambda: self.stack.slide_to(3))

    # -------------------- SEPARATOR --------------------
    def create_separator(self, direction="h"):
        "Line Direction Vertical or Horizontal"
        frame = QFrame()
        frame.setFrameShadow(QFrame.Shadow.Plain)

        if direction.lower().startswith("h"):
            frame.setFrameShape(QFrame.Shape.HLine)
            frame.setFixedHeight(1)
        else:
            frame.setFrameShape(QFrame.Shape.VLine)
            frame.setFixedWidth(1)

        frame.setStyleSheet("background-color: #444;")
        return frame

    # -------------------- NAV BUTTON SETUP --------------------
    def setup_nav_button(self, button: QPushButton, pixmap: QPixmap, text: str):
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setObjectName("navbutton")
        button.setFixedHeight(60)
        button.setToolTip(text)

        # base style for unselected buttons
        default_style = """
            QPushButton {
                color: white;
                background-color: #079fce;
                border: none;
                padding: 5px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #016583;
                border: 1px solid #f53030;
            }
        """
        # selected style
        selected_style = """
            QPushButton {
                color: white;
                background-color: #016583;
                border: 1px solid #f53030;
            }
        """

        button.default_style = default_style
        button.selected_style = selected_style
        button.setStyleSheet(default_style)

        layout = QHBoxLayout(button)
        layout.setContentsMargins(10, 5, 10, 5)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            pixmap.scaled(self.icon_size, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
        )
        text_lbl = QLabel(text)
        text_lbl.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        layout.addStretch()

        button.logo_label = icon_lbl
        button.text_label = text_lbl

        # Connect click to selection handler
        button.clicked.connect(lambda checked, b=button: self.select_nav_button(b))

    def select_nav_button(self, button: QPushButton):
        # reset previous
        if self.selected_nav_btn and self.selected_nav_btn != button:
            self.selected_nav_btn.setStyleSheet(self.selected_nav_btn.default_style)

        # set new selected
        button.setStyleSheet(button.selected_style)
        self.selected_nav_btn = button
    # -------------------- FIXED NAV COLLAPSE --------------------
    def toggle_nav(self):
        start = self.nav_widget.width()
        end = self.nav_width_collapsed if self.nav_expanded else self.nav_width_expanded

        # animate width
        for prop in (b"minimumWidth", b"maximumWidth"):
            anim = QPropertyAnimation(self.nav_widget, prop)
            anim.setDuration(self.anim_duration)
            anim.setStartValue(start)
            anim.setEndValue(end)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim.start()
            setattr(self, f"_anim_{prop}", anim)

        # correct show/hide logic
        new_state = not self.nav_expanded
        for btn in self.nav_buttons:
            btn.text_label.setVisible(new_state)

        # force layout refresh
        self.nav_widget.updateGeometry()
        self.nav_widget.adjustSize()

        self.nav_expanded = new_state

        # correct icon switching
        self.toggle_btn.setIcon(
            self.icon_expand if self.nav_expanded else self.icon_collapse
        )

    def create_taskbar(self):
        # Create status bar
        status = QStatusBar()
        status.setObjectName("mainStatusBar")  # Object name for QSS
        status.setContentsMargins(8, 4, 8, 4)

        # LEFT: USER
        self.login_type = QLabel("USER:")
        self.login_type.setObjectName("statusUser")  # QSS target

        # CENTER
        self.connected_device = QLabel("Devices: 0")
        self.connected_device.setObjectName("statusCenter")  # QSS target
        self.connected_device.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # RIGHT: APP VERSION
        version = QApplication.instance().applicationVersion()
        app_name = QApplication.instance().applicationName()
        self.app_name_label = QLabel(f"{app_name} {version}")
        self.app_name_label.setObjectName("statusVersion")  # QSS target

        # Spacers
        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Add to status bar
        status.addWidget(self.login_type)      # LEFT
        status.addWidget(left_spacer)          # left spacer
        status.addWidget(self.connected_device)    # CENTER
        status.addWidget(right_spacer)         # right spacer
        status.addPermanentWidget(self.app_name_label)  # RIGHT

        # Set status bar
        self.setStatusBar(status)
            
# -------------------- RUN --------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationVersion("0.0.1")
    app.setApplicationName("E-Viotrack")
    event_filter = GlobalActivityLogger()
    app.installEventFilter(event_filter)
    window = E_Viotrack()
    window.show()

    logger = GlobalActivityLogger(log_callback=window.log_page.add_log, throttle_seconds=1)
    app.installEventFilter(logger)

    sys.exit(app.exec())
