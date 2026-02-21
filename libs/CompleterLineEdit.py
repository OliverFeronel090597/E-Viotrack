from PyQt6.QtWidgets import QLineEdit, QCompleter, QListView
from PyQt6.QtCore import Qt, QStringListModel, pyqtSignal
from collections.abc import Iterable

class CompleterLineEdit(QLineEdit):
    selected_driver = pyqtSignal(str)
    def __init__(self, suggestions=None, width=None, parent=None):
        super().__init__(parent)

        if width:
            self.setMaximumWidth(width)

        # Flatten any type of iterable into strings
        self.suggestions = self._flatten_to_strings(suggestions)

        # --- Setup completer ---
        self.completer = QCompleter()
        self.model = QStringListModel(self.suggestions)
        self.completer.setModel(self.model)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)

        # --- Custom styled popup ---
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

        # Connect selection to #print
        self.completer.activated.connect(self._on_completer_selected)

    def _flatten_to_strings(self, data):
        """Recursively flatten iterables and convert everything to strings"""
        result = []
        if data is None:
            return result
        if isinstance(data, str):
            return [data]
        if isinstance(data, Iterable):
            for item in data:
                result.extend(self._flatten_to_strings(item))
        else:
            result.append(str(data))
        return result

    def _on_completer_selected(self, driver):
        """Print the selected item"""
        ##print(f"Selected: {driver}")
        self.selected_driver.emit(driver)

    # # Optional: clear if focus lost and text is not in suggestions
    # def focusOutEvent(self, event):
    #     if self.text() not in self.suggestions:
    #         self.clear()
    #     super().focusOutEvent(event)
