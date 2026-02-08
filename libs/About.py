from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QApplication
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class AboutDialog(QDialog):
    def __init__(self, version, parent=None):
        super().__init__(parent)
        self.setWindowTitle("E-VioTrack")
        self.version = version

        # Theme property (for QSS styling)
        self.setProperty("role", "aboutApp")
        self.style().polish(self)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setLayout(layout)

        # ----------------------
        # LOGO
        # ----------------------
        logo_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_label.setProperty("role", "logo")

        pix = QPixmap(":/resources/E-VioTrack.png").scaled(
            200, 200,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        logo_label.setPixmap(pix)
        logo_layout.addWidget(logo_label)
        layout.addLayout(logo_layout)

        # ----------------------
        # APP INFO
        # ----------------------

        app_info = [
            "<h1>E-VioTrack</h1>",
            f"<h2>Version: {self.version}</h2>",
            "<h3>Developer: Oliver Feronel</h3>",
            "<h3>Owner: Speedy Team</h3>"
        ]

        for item in app_info:
            lbl = QLabel(item)
            lbl.setProperty("role", "app_info")
            layout.addWidget(lbl)

        # ----------------------
        # LICENSE INFO
        # ----------------------
        license_info = [
            '<h3>Qt6 GUI Framework (LGPLv3): <a href="https://www.qt.io/licensing" style="color:#1E90FF;">Qt6 Licensing</a></h3>',
            '<h3>Application License: <a href="https://www.gnu.org/licenses/lgpl-3.0.html" style="color:#1E90FF;">LGPL v3.0</a></h3>',
            '<h3>Written in Python 3.14+</h3>'
        ]

        for item in license_info:
            lbl = QLabel(item)
            lbl.setOpenExternalLinks(True)
            lbl.setProperty("role", "license")
            layout.addWidget(lbl)

        # ----------------------
        # SUPPORT
        # ----------------------
        support_info = [
            '<h3>📧 Support: <a href="mailto:oliver.feronel1@gmail.com" style="color:#1E90FF;">oliver.feronel@gmail.com</a></h3>',
        ]

        for item in support_info:
            lbl = QLabel(item)
            lbl.setOpenExternalLinks(True)
            lbl.setProperty("role", "support")
            layout.addWidget(lbl)

        # Optional: set a fixed width for better appearance
        self.setFixedWidth(400)
