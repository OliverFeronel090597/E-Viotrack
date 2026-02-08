from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer, QObject, QEvent
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QFrame, QStyle
from libs.SlideNotification import SlideNotification


# ============================================================
# NotificationManager (queue + reposition + QSS compatible)
# ============================================================
class NotificationManager(QWidget):
    def __init__(self, parent, icon_name=None, position="left"):
        super().__init__(parent)
        self.notifications = []
        self.icon_name = icon_name
        self.position = position
        self.pending_notifications = []

        parent.installEventFilter(self)

        # Process queue timer
        self.queue_timer = QTimer(self)
        self.queue_timer.setInterval(100)
        self.queue_timer.timeout.connect(self._process_queue)
        self.queue_timer.start()

    def eventFilter(self, watched: QObject, event: QEvent):
        if event.type() == QEvent.Type.Resize:
            self._reposition_existing_only()
        return super().eventFilter(watched, event)

    def show_notification(self, message, icon_new=None):
        self.pending_notifications.append((message, icon_new))

    def _process_queue(self):
        if not self.pending_notifications or any(n.is_animating for n in self.notifications):
            return
        message, icon_new = self.pending_notifications.pop(0)
        self._create_notification(message, icon_new)

    def _create_notification(self, message, icon_new=None):
        notif = SlideNotification(
            message,
            self.parent(),
            icon_name=icon_new if icon_new else self.icon_name,
            position=self.position
        )
        self.notifications.append(notif)
        notif.show()

        self._reposition_existing_only()
        notif.animate(notif.pos())

        QTimer.singleShot(4100, lambda: self.cleanup(notif))

    def cleanup(self, notif):
        if notif in self.notifications:
            self.notifications.remove(notif)
            notif.deleteLater()
            self._reposition_existing_only()

    def _reposition_existing_only(self):
        if not self.notifications:
            return

        bottom_margin = 35   # distance from bottom
        right_margin = 10    # distance from right side
        spacing = 5          # spacing between stacked notifications

        base_y = self.parent().height() - bottom_margin

        for notif in reversed(self.notifications):
            if self.position == "left":
                x = 10  # distance from left, adjust if needed
            else:  # right side
                x = self.parent().width() - notif.width() - right_margin

            notif.move(x, base_y - notif.height())
            base_y -= notif.height() + spacing
