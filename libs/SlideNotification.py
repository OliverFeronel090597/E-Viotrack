from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer
from PyQt6.QtWidgets import QApplication, QLabel, QHBoxLayout, QFrame, QStyle


# ============================================================
# SlideNotification (refactored for parent QSS inheritance)
# ============================================================
class SlideNotification(QFrame):
    def __init__(self, text, parent, icon_name=None, position="left"):
        super().__init__(parent)
        self.position = position
        self.icon_name = icon_name
        self.is_animating = False

        self.setProperty("role", "SlideNotification")
        self.setFixedSize(300, 75)

        # Icon setup
        icon_enum = getattr(QStyle.StandardPixmap, icon_name if icon_name else "SP_MessageBoxInformation")
        icon = QApplication.style().standardIcon(icon_enum)
        pixmap = icon.pixmap(32, 32)

        self.label_icon = QLabel()
        self.label_icon.setPixmap(pixmap)
        self.label_icon.setFixedSize(40, 40)
        self.label_icon.setProperty("role", "SlideNotificationIcon")

        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setProperty("role", "SlideNotificationLabel")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addWidget(self.label_icon)
        layout.addWidget(label)

        # Slide-in animation
        self.slide_in_anim = QPropertyAnimation(self, b"pos", self)
        self.slide_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.slide_in_anim.setDuration(500)
        self.slide_in_anim.finished.connect(lambda: setattr(self, "is_animating", False))

        # Slide-out animation
        self.slide_out_anim = QPropertyAnimation(self, b"pos", self)
        self.slide_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.slide_out_anim.setDuration(500)
        self.slide_out_anim.finished.connect(self.close)

        # Auto-close timer
        self.slide_timer = QTimer(self)
        self.slide_timer.setSingleShot(True)
        self.slide_timer.timeout.connect(self.start_slide_out)

    def animate(self, target_pos: QPoint):
        self.is_animating = True

        # Determine slide-in start position
        start_x = -self.width() if self.position == "left" else self.parent().width()
        start_pos = QPoint(start_x, target_pos.y())
        self.move(start_pos)

        self.slide_in_anim.setStartValue(start_pos)
        self.slide_in_anim.setEndValue(target_pos)
        self.slide_in_anim.start()

        self.slide_timer.start(3000)

    def start_slide_out(self):
        current_y = self.y()
        end_x = -self.width() if self.position == "left" else self.parent().width()
        end_pos = QPoint(end_x, current_y)

        self.slide_out_anim.setStartValue(self.pos())
        self.slide_out_anim.setEndValue(end_pos)
        self.slide_out_anim.start()
