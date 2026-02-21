from PyQt6.QtWidgets import QListWidget, QApplication
from PyQt6.QtCore import Qt
import re


class TagListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._is_manual_scroll = True


    # ---------------- RIGHT CLICK ----------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_manual_scroll != self._is_manual_scroll
            #print(f"_is_manual_scroll {self._is_manual_scroll}")
            return
        super().mousePressEvent(event)


    # ---------------- DOUBLE CLICK = COPY DIGITS ----------------
    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            text = item.text()
            digits = "".join(re.findall(r"\d+", text))

            QApplication.clipboard().setText(digits)
            #print(f"Copied digits: {digits}")

        super().mouseDoubleClickEvent(event)

    # ---------------- BLOCK MOTHER scrollToBottom() ----------------
    def scrollToBottom(self):
        #print("Scroll")
        if self._is_manual_scroll:
            return
        super().scrollToBottom()
