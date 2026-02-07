from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

class AutoCapLineEdit(QLineEdit):
    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        if event.text() and not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            cursor_pos = self.cursorPosition()
            text = self.text()
            capitalized = " ".join(word.capitalize() if word.strip() else word for word in text.split(" "))
            if capitalized != text:
                self.blockSignals(True)
                self.setText(capitalized)
                self.blockSignals(False)
                self.setCursorPosition(cursor_pos)
