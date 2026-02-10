from PyQt6.QtWidgets import QTextEdit, QApplication
from PyQt6.QtCore import Qt

class LineClickTextEdit(QTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setReadOnly(True)

        self.auto_scroll = True   # left-click toggles this

    # --------------------------------------------------------------
    # LEFT CLICK → toggle auto-scroll
    # --------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.auto_scroll = not self.auto_scroll
            event.accept()
            return
        super().mousePressEvent(event)

    # --------------------------------------------------------------
    # LEFT DOUBLE CLICK → copy last word (no scroll)
    # --------------------------------------------------------------
    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mouseDoubleClickEvent(event)

        # keep current scrollbar position to stop the jump
        bar = self.verticalScrollBar()
        old_pos = bar.value()

        cursor = self.cursorForPosition(event.pos())
        cursor.select(cursor.SelectionType.LineUnderCursor)

        line_text = cursor.selectedText().strip()
        last_word = line_text.split(" ")[-1]

        QApplication.clipboard().setText(last_word)

        # restore old scroll position (block auto scroll behavior)
        bar.setValue(old_pos)

        event.accept()

    # --------------------------------------------------------------
    # External call: add text with auto-scroll behavior
    # --------------------------------------------------------------
    def add_line(self, text: str):
        self.append(text)
        if self.auto_scroll:
            self.scroll_to_end()

    # --------------------------------------------------------------
    # Helper
    # --------------------------------------------------------------
    def scroll_to_end(self):
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
