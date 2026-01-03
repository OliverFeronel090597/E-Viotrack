import sys
import threading
import json
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLabel, QCheckBox, QListWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer

PORTS_FILE = "saved_ports.json"

# -------------------- Worker Thread --------------------
class RFIDReaderThread(threading.Thread):
    def __init__(self, port, baudrate=115200, callback=None):
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
                        epc = line.decode(errors="ignore").strip()
                        if epc and self.callback:
                            self.callback(self.port, epc)
                except serial.SerialException as e:
                    print(f"[{self.port}] Serial error:", e)
                    break
        except Exception as e:
            print(f"[{self.port}] Could not open port:", e)
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
            print(f"[{self.port}] Reader stopped")

    def stop(self):
        self.running = False

# -------------------- Qt Signals Wrapper --------------------
class SignalWrapper(QObject):
    tag_read = pyqtSignal(str, str)  # port, epc

# -------------------- GUI --------------------
class RFIDManager(QWidget):
    POLL_INTERVAL_MS = 2000  # Check ports every 2 seconds

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-RFID Manager")
        self.resize(600, 400)
        layout = QVBoxLayout(self)

        self.signals = SignalWrapper()
        self.signals.tag_read.connect(self.on_tag_read)

        # Container for checkboxes
        self.port_layout = QVBoxLayout()
        layout.addLayout(self.port_layout)

        # List for live tags
        self.tag_list = QListWidget()
        layout.addWidget(QLabel("Tags Read:"))
        layout.addWidget(self.tag_list)

        # Internal state
        self.threads = {}     # port -> thread
        self.checkboxes = {}  # port -> QCheckBox
        self.current_ports = set()
        self.saved_ports = self.load_saved_ports()

        # Timer to poll ports
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_ports)
        self.timer.start(self.POLL_INTERVAL_MS)

        self.check_ports()  # initial scan

    # -------------------- Load saved ports --------------------
    def load_saved_ports(self):
        try:
            with open(PORTS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()

    # -------------------- Save current selected ports --------------------
    def save_ports(self):
        ports_to_save = [p for p, cb in self.checkboxes.items() if cb.isChecked()]
        with open(PORTS_FILE, "w") as f:
            json.dump(ports_to_save, f)

    # -------------------- Auto-detect ports --------------------
    def check_ports(self):
        available_ports = set(p.device for p in serial.tools.list_ports.comports())

        # Add new ports
        for port in available_ports - self.current_ports:
            cb = QCheckBox(port)
            cb.stateChanged.connect(self.on_port_checkbox_changed)
            self.port_layout.addWidget(cb)
            self.checkboxes[port] = cb
            print(f"[{port}] Detected new port")

            # Auto-check if previously saved
            if port in self.saved_ports:
                cb.setChecked(True)

        # Remove disconnected ports
        for port in self.current_ports - available_ports:
            print(f"[{port}] Removed port")
            cb = self.checkboxes.pop(port, None)
            if cb:
                self.port_layout.removeWidget(cb)
                cb.deleteLater()
            self.stop_reader(port)

        self.current_ports = available_ports

    # -------------------- Checkbox toggle --------------------
    def on_port_checkbox_changed(self, state):
        cb = self.sender()
        port = cb.text()
        if state == Qt.CheckState.Checked.value:
            self.start_reader(port)
        else:
            self.stop_reader(port)
            # Remove manually unchecked ports from saved list
            if port in self.saved_ports:
                self.saved_ports.remove(port)
        self.save_ports()

    # -------------------- Start reader --------------------
    def start_reader(self, port):
        if port in self.threads:
            return
        thread = RFIDReaderThread(port, callback=lambda p, epc: self.signals.tag_read.emit(p, epc))
        thread.start()
        self.threads[port] = thread
        print(f"[{port}] Reader started")
        self.saved_ports.add(port)
        self.save_ports()

    # -------------------- Stop reader --------------------
    def stop_reader(self, port):
        thread = self.threads.pop(port, None)
        if thread:
            thread.stop()
            thread.join()
            print(f"[{port}] Reader stopped")

    # -------------------- Tag read --------------------
    def on_tag_read(self, port, epc):
        item_text = f"{port} -> {epc}"
        for i in range(self.tag_list.count()):
            if self.tag_list.item(i).text() == item_text:
                return
        self.tag_list.addItem(item_text)

    # -------------------- Clean up --------------------
    def closeEvent(self, event):
        for port in list(self.threads.keys()):
            self.stop_reader(port)
        self.save_ports()
        event.accept()

# -------------------- Run --------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = RFIDManager()
    win.show()
    sys.exit(app.exec())
