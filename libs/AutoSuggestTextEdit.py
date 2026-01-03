from PyQt6.QtWidgets import QTextEdit, QCompleter
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QTextCursor

class SuggestTextEdit(QTextEdit):
    def __init__(self, width, height, items=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setProperty("role", "autoSuggest")
        items = items or []
        self.setPlaceholderText("Comment")

        self.completer = QCompleter(items)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

        popup = self.completer.popup()
        popup.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        popup.setProperty("role", "suggestionPopup")  # 🔹 Role added here
        max_items = min(len(items), 12)
        popup.setMaximumHeight(popup.sizeHintForRow(0) * max_items)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.completer.setWidget(self)

    def insert_completion(self, completion):
        tc = self.textCursor()
        extra = len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, extra)
        tc.insertText(completion + ' ')
        self.setTextCursor(tc)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        # Handle enter key if popup is visible
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.completer.popup().isVisible():
            self.insert_completion(self.completer.currentCompletion() or self.completer.popup().model().index(0, 0).data())
            self.completer.popup().hide()
            event.accept()
            return

        super().keyPressEvent(event)

        # Update completion
        prefix = self.text_under_cursor()
        if prefix and (event.text().isalnum() or event.text() in ('_',)):
            self.completer.setCompletionPrefix(prefix)
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 10)
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

    def text_under_cursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        return tc.selectedText().strip()
