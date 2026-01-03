from PyQt6.QtWidgets import QTableWidget, QAbstractItemView, QTableWidgetItem
from PyQt6.QtCore import Qt, QTimer

class CleanTable(QTableWidget):
    def __init__(self, header=None, rows=0, columns=0, parent=None):
        super().__init__(rows, columns, parent)
        # self.setShowGrid(False)

        self.setHorizontalHeaderLabels(header or [])
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def setItem(self, row, column, item):
        """Center text by default."""
        if isinstance(item, QTableWidgetItem):
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        super().setItem(row, column, item)

    def populate(self, headers: list[str], data: list[list[str]]):
        """Fill table with headers + 2D list of rows."""
        self.clear()
        self.setRowCount(0)
        self.setColumnCount(0)

        # Set headers
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Insert rows
        self.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.setItem(r, c, QTableWidgetItem(str(val)))

        # Resize to contents
        self.resizeColumnsToContents()

        # Force reapply stretch after updates
        self.horizontalHeader().setStretchLastSection(False)
        QTimer.singleShot(0, lambda: self.horizontalHeader().setStretchLastSection(True))

