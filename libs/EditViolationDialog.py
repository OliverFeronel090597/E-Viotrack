from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox, QMessageBox
)
from datetime import datetime
from libs.DatabaseConnector import DatabaseConnector
from libs.CompleterLineEdit import CompleterLineEdit
from libs import GlobalVariable

class EditViolationDialog(QDialog):
    def __init__(self, db: DatabaseConnector, violation=None, parent=None):
        super().__init__(parent)
        self.db = db
        suggestion = self.db.get_all_driver()

        self.violation = violation or {}
        self.setWindowTitle("Edit Violation" if violation else "New Violation")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()

        # ---------------- DRIVER ID ----------------
        layout.addWidget(QLabel("Driver ID"))
        self.driver_id_input = QLineEdit()
        self.driver_id_input.setText(str(self.violation.get("driver_id", "")))
        layout.addWidget(self.driver_id_input)

        # ---------------- DRIVER NAME ----------------
        layout.addWidget(QLabel("Driver Name"))
        self.driver_name_input = CompleterLineEdit(suggestions=suggestion, parent=self)
        self.driver_name_input.setText(str(self.violation.get("driver_name", "")))
        self.driver_name_input.selected_driver.connect(self.on_driver_selected)
        layout.addWidget(self.driver_name_input)

        # ---------------- RFID ----------------
        layout.addWidget(QLabel("RFID Serial"))
        self.rfid_input = QLineEdit()
        self.rfid_input.setText(str(self.violation.get("rfid_serial", "")))
        layout.addWidget(self.rfid_input)

        # ---------------- VIOLATION TYPE ----------------
        layout.addWidget(QLabel("Violation Type"))
        self.violation_type_dropdown = QComboBox()
        self.types_list = db.list_violation_types()
        violation_names = [t["violation_type"] for t in self.types_list]
        violation_names.insert(0, "")
        self.violation_type_dropdown.addItems(violation_names)
        if self.violation.get("violation"):
            index = next((i for i, t in enumerate(self.types_list) if t["violation_type"] == self.violation["violation"]), 0)
            self.violation_type_dropdown.setCurrentIndex(index)
        layout.addWidget(self.violation_type_dropdown)

        # ---------------- VEHICLE ----------------
        layout.addWidget(QLabel("Vehicle"))
        self.vehicle_input = QLineEdit()
        self.vehicle_input.setText(str(self.violation.get("vehicle", "")))
        layout.addWidget(self.vehicle_input)

        # ---------------- DATE ----------------
        layout.addWidget(QLabel("Date (YYYY-MM-DD)"))
        self.date_input = QLineEdit()
        self.date_input.setText(str(self.violation.get("date", datetime.now().strftime("%Y-%m-%d"))))
        layout.addWidget(self.date_input)

        # ---------------- DUE DATE ----------------
        layout.addWidget(QLabel("Due Date (YYYY-MM-DD)"))
        self.due_date_input = QLineEdit()
        self.due_date_input.setText(str(self.violation.get("due_date", datetime.now().strftime("%Y-%m-%d"))))
        layout.addWidget(self.due_date_input)

        # ---------------- AMOUNT ----------------
        layout.addWidget(QLabel("Amount"))
        self.amount_input = QLineEdit()
        self.amount_input.setText(str(self.violation.get("amount", 0)))
        self.amount_input.setReadOnly(True)  # amount comes from violation type
        layout.addWidget(self.amount_input)

        # ---------------- BUTTONS ----------------
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # ---------------- UPDATE AMOUNT ----------------
        self.violation_type_dropdown.currentIndexChanged.connect(self.update_amount)

        # ---------------- LOCK FIELDS ----------------
        if self.violation:  # edit mode
            # Only allow editing violation type and date
            self.driver_id_input.setReadOnly(True)
            self.driver_name_input.setReadOnly(True)
            self.rfid_input.setReadOnly(True)
            self.vehicle_input.setReadOnly(True)
            self.due_date_input.setReadOnly(True)
            self.amount_input.setReadOnly(True)


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
                violation=violation,
                paid='unpaid',
                due_date=due_date
            )
            print(f"${GlobalVariable.user_login} Update violation {violation} of {driver_name}")
        else:
            # add
            self.db.add_violation(
                driver_name=driver_name,
                driver_id=driver_id,
                rfid_serial=rfid,
                violation=violation,
                vehicle=vehicle,
                date=date,
                amount=amount,
                due_date=due_date,
                paid="unpaid"
            )
            print(f"${GlobalVariable.user_login} Add violation {violation} of {driver_name}")
        self.accept()

    # -------------------------------
    def on_driver_selected(self, driver_name: str):
        """
        Auto-fill other fields when a driver is selected
        """
        drivers = self.db.select_all_driver(driver_name)  # returns list of tuples

        driver_dict = None
        for d in drivers:
            if d[3] == driver_name:  # driver_name is at index 3
                driver_dict = {
                    "id": d[0],
                    "user_id": d[1],
                    "rfid_serial": d[2],
                    "driver_name": d[3],
                    "date_added": d[4],
                    "vehicle": d[5]
                }
                break

        if not driver_dict:
            return

        self.driver_id_input.setText(str(driver_dict["user_id"]))
        self.rfid_input.setText(str(driver_dict["rfid_serial"]))
        self.vehicle_input.setText(str(driver_dict["vehicle"]))

        # Optional: reset violation type & amount
        self.violation_type_dropdown.setCurrentIndex(0)
        self.update_amount()
