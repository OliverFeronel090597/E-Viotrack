from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QMessageBox
)
from libs.UniqueID import generate_unique_id
try:
    from libs.AutoCapital import AutoCapLineEdit
except ImportError:
    from AutoCapital import AutoCapLineEdit


class EditDriverDialog(QDialog):
    def __init__(self, db, driver_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.driver_data = driver_data or {}
        self.unique_id = generate_unique_id()
        self.setWindowTitle("Edit Driver" if driver_data else "New Driver")
        self.setMinimumWidth(350)
        layout = QVBoxLayout()
        layout.setSpacing(6)

        layout.addWidget(QLabel("Driver ID"))
        self.driver_id_input = QLineEdit()
        self.driver_id_input.setText(self.driver_data.get("driver_id") or self.unique_id)
        self.driver_id_input.setReadOnly(bool(driver_data))
        layout.addWidget(self.driver_id_input)

        layout.addWidget(QLabel("RFID Serial"))
        self.rfid_input = QLineEdit()
        self.rfid_input.setText(self.driver_data.get("rfid_serial", ""))
        layout.addWidget(self.rfid_input)

        layout.addWidget(QLabel("Full Name"))
        self.full_name_input = AutoCapLineEdit()
        self.full_name_input.setText(self.driver_data.get("full_name", ""))
        layout.addWidget(self.full_name_input)

        layout.addWidget(QLabel("Vehicle"))
        self.vehicle_input = QLineEdit()
        self.vehicle_input.setText(self.driver_data.get("vehicle", ""))
        layout.addWidget(self.vehicle_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_driver)
        btn_layout.addWidget(self.save_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_driver(self):
        driver_id = self.driver_id_input.text().strip()
        rfid = self.rfid_input.text().strip()
        name = self.full_name_input.text().strip()
        vehicle = self.vehicle_input.text().strip()
        if not driver_id or not rfid or not name or not vehicle:
            QMessageBox.warning(self, "Error", "All fields required")
            return
        if self.driver_data:
            self.db.update_driver(driver_id, rfid_serial=rfid, full_name=name, vehicle=vehicle)
        else:
            self.db.add_driver(driver_id, rfid, name, vehicle)
        self.accept()
