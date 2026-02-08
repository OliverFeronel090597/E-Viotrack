from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox, QMessageBox
)
from datetime import datetime
from libs.DatabaseConnector import DatabaseConnector


class EditViolationDialog(QDialog):
    def __init__(self, db: DatabaseConnector, violation=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.violation = violation or {}
        self.setWindowTitle("Edit Violation" if violation else "New Violation")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Driver ID"))
        self.driver_id_input = QLineEdit()
        self.driver_id_input.setText(str(self.violation.get("driver_id", "")))
        layout.addWidget(self.driver_id_input)

        layout.addWidget(QLabel("Driver Name"))
        self.driver_name_input = QLineEdit()
        self.driver_name_input.setText(str(self.violation.get("driver_name", "")))
        layout.addWidget(self.driver_name_input)

        layout.addWidget(QLabel("RFID Serial"))
        self.rfid_input = QLineEdit()
        self.rfid_input.setText(str(self.violation.get("rfid_serial", "")))
        layout.addWidget(self.rfid_input)

        layout.addWidget(QLabel("Violation Type"))
        self.violation_type_dropdown = QComboBox()
        self.types_list = db.list_violation_types()
        self.violation_type_dropdown.addItems([t["violation_type"] for t in self.types_list])
        if self.violation.get("violation"):
            index = next((i for i, t in enumerate(self.types_list) if t["violation_type"] == self.violation["violation"]), 0)
            self.violation_type_dropdown.setCurrentIndex(index)
        layout.addWidget(self.violation_type_dropdown)

        layout.addWidget(QLabel("Vehicle"))
        self.vehicle_input = QLineEdit()
        self.vehicle_input.setText(str(self.violation.get("vehicle", "")))
        layout.addWidget(self.vehicle_input)

        layout.addWidget(QLabel("Date (YYYY-MM-DD)"))
        self.date_input = QLineEdit()
        self.date_input.setText(str(self.violation.get("date", datetime.now().strftime("%Y-%m-%d"))))
        layout.addWidget(self.date_input)

        layout.addWidget(QLabel("Due Date (YYYY-MM-DD)"))
        self.due_date_input = QLineEdit()
        self.due_date_input.setText(str(self.violation.get("due_date", datetime.now().strftime("%Y-%m-%d"))))
        layout.addWidget(self.due_date_input)

        layout.addWidget(QLabel("Amount"))
        self.amount_input = QLineEdit()
        self.amount_input.setText(str(self.violation.get("amount", 0)))
        self.amount_input.setReadOnly(True)  # amount comes from violation type
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

        # Update amount when violation type changes
        self.violation_type_dropdown.currentIndexChanged.connect(self.update_amount)

    def update_amount(self):
        violation = self.violation_type_dropdown.currentText()
        amount = next((t["amount"] for t in self.types_list if t["violation_type"] == violation), 0)
        self.amount_input.setText(str(amount))

    def save(self):
        driver_id = self.driver_id_input.text().strip()
        driver_name = self.driver_name_input.text().strip()
        rfid = self.rfid_input.text().strip()
        violation = self.violation_type_dropdown.currentText()
        vehicle = self.vehicle_input.text().strip()
        date = self.date_input.text().strip()
        due_date = self.due_date_input.text().strip()
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Amount must be a number")
            return

        if not all([driver_id, driver_name, rfid, violation, vehicle, date, due_date]):
            QMessageBox.warning(self, "Error", "All fields required")
            return

        if self.violation:
            # edit
            self.db.update_violation(
                self.violation["id"],
                user="Admin",
                violation=violation,
                paid=self.violation.get("paid", 0),
                due_date=due_date
            )
        else:
            # add
            self.db.add_violation(
                user="Admin",
                driver_name=driver_name,
                driver_id=driver_id,
                rfid_serial=rfid,
                violation=violation,
                vehicle=vehicle,
                date=date,
                amount=amount,
                due_date=due_date,
                paid=0
            )
        self.accept()
