from PyQt6.QtWidgets import QLineEdit, QCompleter, QListView
from PyQt6.QtCore import Qt, QStringListModel

class CompleterLineEdit(QLineEdit):
    def __init__(self, suggestions, width, callback, enter_func=False, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(width)
        self.suggestions = suggestions
        self.enter_func = enter_func
        self.enter_callback = callback  # Function to call on select/Enter

        # Setup completer
        self.completer = QCompleter()
        self.model = QStringListModel(self.suggestions)
        self.completer.setModel(self.model)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)

        # Custom styled popup
        popup = QListView()
        popup.setObjectName("completerPopup")
        popup.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        popup.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        popup.setStyleSheet("""
            QListView#completerPopup {
                background-color: #ffffff;
                border: 1px solid #7f8c8d;
                padding: 4px;
                font: 12px "Segoe UI";
                selection-background-color: #3498db;
                selection-color: #ffffff;
                outline: none;
                border-radius: 3px;
                color: #000000;
            }
            QListView#completerPopup::item {
                padding: 4px 8px;
            }
        """)
        self.completer.setPopup(popup)
        self.setCompleter(self.completer)

        # Connect signal
        self.completer.activated.connect(self._on_completer_selected)

    def _on_completer_selected(self, text):
        if self.enter_callback:
            self.enter_callback(text, "select")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.enter_func and self.text().strip():
                if self.enter_callback:
                    self.enter_callback(self.text().strip(), "enter")
                return  # Don't pass to base to avoid duplicate triggering
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        if not self.enter_func and self.text() not in self.suggestions:
            self.clear()
        super().focusOutEvent(event)
