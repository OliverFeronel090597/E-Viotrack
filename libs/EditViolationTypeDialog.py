from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QMessageBox
)
from libs.AutoCapital import AutoCapLineEdit
from libs.DatabaseConnector import DatabaseConnector


class EditViolationTypeDialog(QDialog):
    def __init__(self, db: DatabaseConnector, vtype_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.vtype_data = vtype_data or {}
        self.setWindowTitle("Edit Violation Type" if vtype_data else "New Violation Type")
        self.setMinimumWidth(300)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Violation Type"))
        self.type_input = AutoCapLineEdit()
        self.type_input.setText(self.vtype_data.get("violation_type", ""))
        layout.addWidget(self.type_input)

        layout.addWidget(QLabel("Amount"))
        self.amount_input = QLineEdit()
        self.amount_input.setText(str(self.vtype_data.get("amount", "")))
        layout.addWidget(self.amount_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save(self):
        vtype = self.type_input.text().strip()
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Amount must be a number")
            return
        if not vtype:
            QMessageBox.warning(self, "Error", "Violation Type required")
            return

        if self.vtype_data:
            self.db.update_violation_type(self.vtype_data["id"], violation_type=vtype, amount=amount)
        else:
            self.db.add_violation_type(vtype, amount)
        self.accept()
