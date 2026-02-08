from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QPushButton, 
    QMessageBox
)
from PyQt6.QtCore import Qt
import serial
import serial.tools.list_ports
from libs.DatabaseConnector import DatabaseConnector
from libs.SerialReaderThread import SerialReaderThread


# ---------------- SINGLE SERIAL WIDGET ----------------
class SerialWidget(QWidget):
    def __init__(self, db: DatabaseConnector, remove_callback=None):
        super().__init__()
        self.setObjectName("HomePageRoot")

        self.db = db
        self.remove_callback = remove_callback
        self.serial_thread = None

        layout = QVBoxLayout(self)

        # Port selection + connect + remove
        port_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_serial)
        port_layout.addWidget(self.connect_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_self)
        port_layout.addWidget(self.remove_button)
        layout.addLayout(port_layout)

        # L1 input
        self.input_l1 = QLineEdit()
        self.input_l1.setPlaceholderText("Scan or type RFID serial L1...")
        layout.addWidget(self.input_l1)
        self.input_l1.textChanged.connect(lambda: self.on_serial_changed(self.input_l1))

        # Violation table
        self.violation_table = QTableWidget()
        self.violation_table.setColumnCount(2)
        self.violation_table.setHorizontalHeaderLabels(["Violation ID", "Violation"])
        layout.addWidget(self.violation_table)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)

    def toggle_serial(self):
        if self.serial_thread and self.serial_thread.isRunning():
            self.disconnect_serial()
        else:
            port = self.port_combo.currentText()
            if not port:
                QMessageBox.warning(self, "Serial Error", "No serial port selected")
                return
            self.serial_thread = SerialReaderThread(port)
            self.serial_thread.data_received.connect(self.update_input_l1)
            self.serial_thread.error_occurred.connect(self.handle_serial_error)
            self.serial_thread.start()
            self.connect_button.setText("Disconnect")

    def update_input_l1(self, serial_data: str):
        self.input_l1.setText(serial_data)

    def on_serial_changed(self, line_edit: QLineEdit):
        serial = line_edit.text().strip()
        self.violation_table.setRowCount(0)
        if not serial:
            return

        driver = self.db.get_driver_by_rfid(serial)
        if not driver:
            self.violation_table.setRowCount(1)
            self.violation_table.setItem(0, 0, QTableWidgetItem("None"))
            self.violation_table.setItem(0, 1, QTableWidgetItem("None"))
            return

        full_name = driver[3]
        violations = self.db.get_violations_by_user(full_name)
        if not violations:
            self.violation_table.setRowCount(1)
            self.violation_table.setItem(0, 0, QTableWidgetItem("None"))
            self.violation_table.setItem(0, 1, QTableWidgetItem("None"))
            return

        self.violation_table.setRowCount(len(violations))
        for idx, (vid, vtext) in enumerate(violations):
            self.violation_table.setItem(idx, 0, QTableWidgetItem(str(vid)))
            self.violation_table.setItem(idx, 1, QTableWidgetItem(vtext))

    def handle_serial_error(self, msg: str):
        QMessageBox.warning(self, "Serial Error", msg)
        self.disconnect_serial()

    def disconnect_serial(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None
        self.connect_button.setText("Connect")

    def remove_self(self):
        self.disconnect_serial()
        if self.remove_callback:
            self.remove_callback(self)
        self.setParent(None)
