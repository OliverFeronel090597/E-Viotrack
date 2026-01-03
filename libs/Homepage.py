from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QTextEdit, QFrame, QMessageBox, QTreeView, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QCursor
from typing import Dict, Any
from libs.DatabaseConnector import DatabaseConnector
from libs.Imagelabel import AutoImageLabel


class ViolationTree(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ViolationTree")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # <-- no focus rectangle

        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels([
            "Driver Name", "Driver ID", "RFID", "Violation", "Vehicle", "Amount", "Date", "Due Date", "Paid"
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


class HomePage(QWidget):
    def __init__(self, db: DatabaseConnector):
        super().__init__()
        self.db = db
        self.setObjectName("HomePage")
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.main_layout)

        self.init_top_row()
        self.init_violation_tree()

    def init_top_row(self):
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        top_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(top_row)

        self.logo_label = AutoImageLabel(r"img/E-VioTrack.png", circle=True, size=(200, 200))
        top_row.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignTop)

        self.quote_card = QFrame()
        self.quote_card.setObjectName("QuoteCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(5)
        self.quote_card.setLayout(card_layout)

        self.quote_area = QTextEdit()
        self.quote_area.setObjectName("QuoteText")
        self.quote_area.setReadOnly(True)
        self.quote_area.setMinimumSize(500, 170)
        self.quote_area.viewport().setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        self.quote_area.setHtml("""
            <h2>E-Viotrack</h2>
            <p>“No escape, no excuses — violations get tagged.”</p>
            <p>“Drive smart. The system doesn’t blink.”</p>
            <p>“Every violation leaves a signal.”</p>
        """)
        card_layout.addWidget(self.quote_area)
        top_row.addWidget(self.quote_card, alignment=Qt.AlignmentFlag.AlignTop)

    def init_violation_tree(self):
        self.violation_tree = ViolationTree()
        self.main_layout.addWidget(self.violation_tree)

        self.delete_btn = QPushButton("Delete Selected Violation")
        self.delete_btn.setObjectName("DeleteViolationBtn")
        self.delete_btn.clicked.connect(self.violation_tree.remove_selected_violation)
        self.delete_btn.hide()
        print("[INFO] Delete button hide from Homepage class as it will not be use maybe in the functure")

        self.main_layout.addWidget(self.delete_btn)

    def handle_add_violation(self, rfid=None):
        print(rfid)
        if not rfid:
            QMessageBox.warning(self, "Input Error", "Please enter RFID.")
            return

        active_violations = self.db.get_active_violations_by_rfid(rfid)
        if not active_violations:
            #QMessageBox.information(self, "No Violations", f"No active violations found for RFID {rfid}.")
            return

        for violation in active_violations:
            self.violation_tree.add_violation(violation, on_top=False)