import sys
import threading
import json
import serial
import serial.tools.list_ports

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QCheckBox, QListWidget, QHBoxLayout, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer

PORTS_FILE = "saved_ports.json"

BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400]


# -------------------- Reader Thread --------------------
class RFIDReaderThread(threading.Thread):
    def __init__(self, port, baudrate, callback=None):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.running = False
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.5)
            self.running = True

            while self.running:
                try:
                    line = self.ser.readline()
                    if line:
                        tag = line.decode(errors="ignore").strip()
                        if tag and self.callback:
                            self.callback(self.port, tag)
                except serial.SerialException as e:
                    print(f"[{self.port}] Serial error:", e)
                    break

        except Exception as e:
            print(f"[{self.port}] Cannot open:", e)

        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
            print(f"[{self.port}] Thread stopped")

    def stop(self):
        self.running = False


# -------------------- Qt Signal Wrapper --------------------
class SignalWrapper(QObject):
    tag_read = pyqtSignal(str, str)   # port, tag

class RFIDManager(QWidget):
    POLL_INTERVAL_MS = 2000

    def __init__(self, upfdate_rfid):
        super().__init__()
        self.setWindowTitle("Multi-RFID Manager")
        self.resize(600, 450)

        # ---- OBJECT NAME FOR QSS ----
        self.setObjectName("rfidManager")

        self.upfdate_rfid = upfdate_rfid

        layout = QVBoxLayout(self)

        # --- Signals ---
        self.signals = SignalWrapper()
        self.signals.tag_read.connect(self.on_tag_read)

        # --- Storage ---
        self.threads = {}
        self.checkboxes = {}
        self.combos = {}
        self.current_ports = set()
        self.saved_ports = self.load_saved_ports()

        # --- Port list container ---
        self.port_container = QVBoxLayout()
        port_container_widget = QWidget()
        port_container_widget.setLayout(self.port_container)
        port_container_widget.setObjectName("portContainer")
        layout.addWidget(port_container_widget)

        # --- Read tags label ---
        lbl = QLabel("Read Tags:")
        lbl.setObjectName("rfidReadLabel")
        layout.addWidget(lbl)

        # --- Tag list widget ---
        self.tag_list = QListWidget()
        self.tag_list.setObjectName("rfidTagList")
        layout.addWidget(self.tag_list)

        # --- Timer for auto port scan ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_ports)
        self.timer.start(self.POLL_INTERVAL_MS)

        self.check_ports()

    # -------------------- Load / Save --------------------
    def load_saved_ports(self):
        try:
            with open(PORTS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    def save_ports(self):
        data = {}
        for port, cb in self.checkboxes.items():
            if cb.isChecked():
                data[port] = {"baud": int(self.combos[port].currentText())}
        with open(PORTS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # -------------------- Port Polling --------------------
    def check_ports(self):
        available_ports = set(p.device for p in serial.tools.list_ports.comports())

        # Added ports
        for port in available_ports - self.current_ports:
            self.add_port_widget(port)

        # Removed ports
        for port in self.current_ports - available_ports:
            self.remove_port_widget(port)

        self.current_ports = available_ports

    # -------------------- UI for each port --------------------
    def add_port_widget(self, port):
        row = QHBoxLayout()
        row_widget = QWidget()
        row_widget.setLayout(row)
        row_widget.setObjectName("portRow")

        cb = QCheckBox(port)
        cb.setObjectName("portCheckBox")
        cb.stateChanged.connect(self.on_port_checkbox)
        self.checkboxes[port] = cb
        row.addWidget(cb)

        combo = QComboBox()
        combo.setObjectName("baudRateCombo")
        for b in BAUD_RATES:
            combo.addItem(str(b))
        combo.setCurrentText("115200")
        combo.currentIndexChanged.connect(lambda _: self.on_baud_changed(port))
        self.combos[port] = combo
        row.addWidget(combo)

        self.port_container.addWidget(row_widget)

        print(f"[{port}] Detected")

        # Auto reconnect if saved
        if port in self.saved_ports:
            combo.setCurrentText(str(self.saved_ports[port]["baud"]))
            cb.setChecked(True)

    def remove_port_widget(self, port):
        print(f"[{port}] Removed")
        cb = self.checkboxes.pop(port, None)
        combo = self.combos.pop(port, None)

        if cb:
            cb.parentWidget().deleteLater()

        self.stop_reader(port)

    # -------------------- Checkbox Events --------------------
    def on_port_checkbox(self, state):
        cb = self.sender()
        port = cb.text()

        if state == Qt.CheckState.Checked.value:
            baud = int(self.combos[port].currentText())
            self.start_reader(port, baud)
        else:
            self.stop_reader(port)

        self.save_ports()

    def on_baud_changed(self, port):
        if port in self.threads:
            print(f"[{port}] Baud changed – restarting thread")
            self.stop_reader(port)
            self.start_reader(port, int(self.combos[port].currentText()))
        self.save_ports()

    # -------------------- Thread Control --------------------
    def start_reader(self, port, baud):
        if port in self.threads:
            return

        thread = RFIDReaderThread(
            port, baud,
            callback=lambda p, t: self.signals.tag_read.emit(p, t)
        )
        thread.start()
        self.threads[port] = thread

        print(f"[{port}] Started @ {baud} baud")

    def stop_reader(self, port):
        thread = self.threads.pop(port, None)
        if thread:
            thread.stop()
            thread.join()
            print(f"[{port}] Stopped")

    # -------------------- Tag Display --------------------
    def on_tag_read(self, port, tag):
        self.tag_list.addItem(f"{port} -> {tag}")

        try:
            if hasattr(self.upfdate_rfid, "handle_add_violation"):
                self.upfdate_rfid.handle_add_violation(tag)
        except Exception as e:
            print("RFID process error:", e)

    # -------------------- Cleanup --------------------
    def closeEvent(self, event):
        for port in list(self.threads.keys()):
            self.stop_reader(port)
        self.save_ports()
        event.accept()
