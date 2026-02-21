from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtGui import QMouseEvent, QKeyEvent
from datetime import datetime, timedelta

class GlobalActivityLogger(QObject):
    """
    Event filter to log all relevant user interactions.
    Repeated identical events within 1 second are suppressed.
    """
    def __init__(self, log_callback=None, throttle_seconds=1.0):
        super().__init__()
        self.log_callback = log_callback
        self.throttle_seconds = throttle_seconds
        self._last_event_hash = None
        self._last_event_time = datetime.min

    def log(self, msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        if self.log_callback:
            self.log_callback(full_msg)
        # else:
        #     #print(full_msg)

    def _should_log(self, event_hash: str) -> bool:
        now = datetime.now()
        if event_hash == self._last_event_hash and (now - self._last_event_time) < timedelta(seconds=self.throttle_seconds):
            return False
        self._last_event_hash = event_hash
        self._last_event_time = now
        return True

    def eventFilter(self, obj: QObject, event: QEvent):
        event_type = event.type()

        # Mouse press
        if isinstance(event, QMouseEvent) and event_type == QEvent.Type.MouseButtonPress:
            btn = event.button()
            btn_name = {
                Qt.MouseButton.LeftButton: "Left",
                Qt.MouseButton.RightButton: "Right",
                Qt.MouseButton.MiddleButton: "Middle",
            }.get(btn, str(btn))

            event_hash = f"MOUSE-{obj.__class__.__name__}-{obj.objectName()}-{btn_name}"

            if self._should_log(event_hash):
                self.log(
                    f"[MOUSE PRESS] Widget={obj.__class__.__name__} objectName='{obj.objectName()}' Button={btn_name}"
                )

        # Key press
        elif isinstance(event, QKeyEvent) and event_type == QEvent.Type.KeyPress:
            key = event.key()
            event_hash = f"KEY-{obj.__class__.__name__}-{obj.objectName()}-{key}"

            if self._should_log(event_hash):
                self.log(
                    f"[KEY PRESS] Widget={obj.__class__.__name__} objectName='{obj.objectName()}' Key={key}"
                )

        return False
