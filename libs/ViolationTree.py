from PyQt6.QtWidgets import (
    QTreeView, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from typing import Dict, Any


class ViolationTree(QTreeView):
    driver_clicked = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ViolationTree")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # <-- no focus rectangle

        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels([
            "Driver Name", "Driver ID", "RFID", "Violation", "Vehicle", "Amount", "Date", "Due Date", "Status"
        ])
        self.setModel(self.tree_model)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)

        header = self.header()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)

        # Connect the click signal
        self.clicked.connect(self.on_item_clicked)

    def clear_tree(self):
        self.tree_model.removeRows(0, self.tree_model.rowCount())

    def add_violation(self, violation: Dict[str, Any], on_top: bool = True):
        if not violation.get("violation"):
            return

        driver_id = violation["driver_id"]
        driver_name = violation["driver_name"]
        parent_item = None

        # Check for existing driver node
        for row in range(self.tree_model.rowCount()):
            item = self.tree_model.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == driver_id:
                parent_item = item
                break

        # Child row data for uniqueness check
        child_data = (
            str(violation.get("driver_id", "")),
            str(violation.get("rfid_serial", "")),
            str(violation.get("violation", "")),
            str(violation.get("vehicle", "")),
            str(violation.get("amount", "")),
            str(violation.get("date", "")),
            str(violation.get("due_date", "")),
            str(violation.get("paid", ""))
        )

        # Check duplicates under this driver
        if parent_item:
            for r in range(parent_item.rowCount()):
                existing = tuple(parent_item.child(r, c).text() for c in range(1, 9))  # skip first column
                if existing == child_data:
                    return  # Duplicate found

        # Create child items
        child_items = [QStandardItem("")] + [QStandardItem(x) for x in child_data]
        for c in child_items:
            c.setEditable(False)

        if parent_item:
            if on_top:
                parent_item.insertRow(0, child_items)
            else:
                parent_item.appendRow(child_items)
        else:
            new_parent = QStandardItem(driver_name)
            new_parent.setEditable(False)
            new_parent.setData(driver_id, Qt.ItemDataRole.UserRole)
            new_parent.appendRow(child_items)

            if on_top:
                self.tree_model.insertRow(0, new_parent)
            else:
                self.tree_model.appendRow(new_parent)

        self.expandAll()

    def remove_selected_violation(self):
        index = self.currentIndex()
        if not index.isValid():
            return

        if index.parent().isValid():
            self.tree_model.removeRow(index.row(), index.parent())
        else:
            self.tree_model.removeRow(index.row())

    def on_item_clicked(self, index: QModelIndex):
        if not index.isValid():
            return

        # Only emit for top-level items (driver names)
        if not index.parent().isValid():
            driver_name = self.tree_model.itemFromIndex(index).text()
            # Emit the signal
            self.driver_clicked.emit(driver_name)