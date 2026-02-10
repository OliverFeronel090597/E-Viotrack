import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox,
    QTextEdit, QHBoxLayout, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QThread
from datetime import datetime
from libs.DatabaseConnector import DatabaseConnector
from libs.RFIDWorker import RFIDWorker
from libs.LineClickTextEdit import LineClickTextEdit

BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400]


# ===================== RFID Manager =====================
class RFIDManager(QWidget):
    POLL_INTERVAL_MS = 2000
    MAX_TAG_LINES_DEFAULT = 1000  # fixed default

    def __init__(self, upfdate_rfid, db: DatabaseConnector, connected_device: QLabel):
        super().__init__()
        self.setWindowTitle("Multi-RFID Manager")
        self.resize(600, 450)

        self.connected_device = connected_device

        self.db = db
        self.upfdate_rfid = upfdate_rfid

        self.threads = {}    # port -> QThread
        self.workers = {}    # port -> RFIDWorker
        self.checkboxes = {} # port -> QCheckBox
        self.combos = {}     # port -> QComboBox
        self.prev_comport_len = 0
        self.current_ports = set()

        layout = QVBoxLayout(self)

        # --- Port container ---
        self.port_container = QVBoxLayout()
        pc_widget = QWidget()
        pc_widget.setObjectName("portContainer")
        pc_widget.setLayout(self.port_container)
        layout.addWidget(pc_widget)

        # --- Max tag lines (read-only, default) ---
        settings_row = QHBoxLayout()
        lbl_ml = QLabel("Max Tag Lines:")
        lbl_ml.setObjectName("maxLineLabel")
        self.max_lines_edit = QLineEdit(str(self.MAX_TAG_LINES_DEFAULT))
        self.max_lines_edit.setObjectName("maxLineEdit")
        self.max_lines_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.max_lines_edit.setReadOnly(True)
        settings_row.addWidget(lbl_ml)
        settings_row.addWidget(self.max_lines_edit)
        layout.addLayout(settings_row)

        # --- Tag list ---
        lbl_tags = QLabel("Read Tags:")
        lbl_tags.setObjectName("tagsLabel")
        layout.addWidget(lbl_tags)

        self.tag_list = LineClickTextEdit(parent=self)
        self.tag_list.setObjectName("rfidTagList")
        layout.addWidget(self.tag_list)

        # --- Auto scan timer ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_ports)
        self.timer.start(self.POLL_INTERVAL_MS)

        self.check_ports()  # initial scan

    # -------------------- Port scan --------------------
    def check_ports(self):
        # Get all serial ports
        ports = serial.tools.list_ports.comports()

        # Only keep external USB-Serial ports (skip Bluetooth / virtual COMs)
        valid_ports = []
        for p in ports:
            hwid = getattr(p, "hwid", "").upper()
            if "BTHENUM" in hwid or "VIRTUAL" in hwid:
                continue
            valid_ports.append(p)

        available = {p.device for p in valid_ports}
        if len(available) != self.prev_comport_len:
            print("Available USB-Serial ports:", available)
            self.prev_comport_len = len(available)

        # Add new ports
        for port in available - self.current_ports:
            self.add_port_widget(port)

        # Remove missing ports
        for port in self.current_ports - available:
            self.remove_port_widget(port)

        self.update_device_counters()
        self.current_ports = available


    # -------------------- UI per port --------------------
    def add_port_widget(self, port):
        row = QHBoxLayout()
        widget = QWidget()
        widget.setObjectName(f"portRow_{port}")
        widget.setLayout(row)

        cb = QCheckBox(port)
        cb.setObjectName("portCheckBox")
        cb.stateChanged.connect(self.on_port_checkbox)
        self.checkboxes[port] = cb
        row.addWidget(cb)

        combo = QComboBox()
        combo.addItems([str(b) for b in BAUD_RATES])
        combo.setCurrentText("115200")
        combo.currentIndexChanged.connect(lambda _: self.on_baud_changed(port))
        combo.setObjectName("baudRateCombo")
        self.combos[port] = combo
        row.addWidget(combo)

        self.port_container.addWidget(widget)
        print(f"[{port}] Detected")

        # Load DB
        db_port = self.db.get_comport(port)
        if db_port:
            combo.setCurrentText(db_port["baudrate"])
            cb.setChecked(True)
            combo.setDisabled(True)  # disable when connected

    def remove_port_widget(self, port):
        print(f"[{port}] Removed")
        cb : QCheckBox = self.checkboxes.pop(port, None)
        combo : QComboBox = self.combos.pop(port, None)
        if cb:
            cb.parentWidget().deleteLater()
        self.stop_reader(port)

    # -------------------- Checkbox + Baud --------------------
    def on_port_checkbox(self, state):
        cb = self.sender()
        port = cb.text()
        combo : QComboBox = self.combos.get(port)
        if not combo:
            return
        baud = combo.currentText()

        if state == Qt.CheckState.Checked.value:
            if port not in self.threads:
                self.start_reader(port, int(baud))
            if self.db.get_comport(port):
                self.db.update_comport(port, baud)
            else:
                self.db.add_comport(port, baud)
            combo.setDisabled(True)
        else:
            self.stop_reader(port)
            self.db.delete_comport(port)
            combo.setDisabled(False)

    def on_baud_changed(self, port):
        combo : QComboBox = self.combos.get(port)
        if not combo or port not in self.threads:
            return
        # Restart reader with new baud
        self.stop_reader(port)
        self.start_reader(port, int(combo.currentText()))
        self.db.update_comport(port, combo.currentText())

    # -------------------- QThread control --------------------
    def start_reader(self, port, baud):
        if port in self.workers:  # check workers, not threads
            return

        # Create worker (thread is internal)
        worker = RFIDWorker(port, baud)

        # Connect signals
        # worker.tag_signal.connect(lambda p, t: print(p, t))  # optional debug
        #worker.finished.connect(lambda p: print(p, "finished"))
        worker.tag_signal.connect(self.on_tag_read)
        worker.finished.connect(self.on_worker_finished)

        # Store references
        self.workers[port] = worker
        self.threads[port] = worker.thread  # optional, if you need reference

        # Start worker (thread managed internally)
        worker.start()

        print(f"[{port}] RFIDWorker started @ {baud}")
        self.update_device_counters()


    def stop_reader(self, port):
        """Safely stop a worker + thread"""
        worker = self.workers.get(port)
        thread = self.threads.get(port)

        if not worker or not thread:
            return

        print(f"[{port}] Stopping reader...")

        try:
            worker.stop()
        except:
            pass

        # ALWAYS quit the thread event loop
        thread.quit()

        # WAIT UNTIL IT FULLY STOPS  (no timeout)
        thread.wait()

        print(f"[{port}] Thread fully stopped")

        # Now safe to delete references
        self.workers.pop(port, None)
        self.threads.pop(port, None)

        self.update_device_counters()


    def on_worker_finished(self, port):
        """Worker ended → finish cleanup by stopping thread properly"""
        print(f"[{port}] Worker finished")

        # Don't delete thread here — call stop_reader (safe path)
        self.stop_reader(port)

    # -------------------- Tag display --------------------
    def on_tag_read(self, port, tag):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.tag_list.append(f"{timestamp} [{port}] -------------> {tag}")

        try:
            if hasattr(self.upfdate_rfid, "handle_add_violation") and tag:
                self.upfdate_rfid.handle_add_violation(tag)
        except Exception as e:
            print("RFID process error:", e)

    def update_device_counters(self):
        running = 0
        not_running = 0
        not_connected = 0

        active_ports = self.current_ports
        db_ports = {p["port"] for p in self.db.list_comports()}

        # Running = thread alive
        running = len(self.threads)

        # Not running = Enabled via checkbox but worker not alive
        for port, cb in self.checkboxes.items():
            if cb.isChecked() and port not in self.threads:
                not_running += 1

        # Not connected = DB saved ports that are not physically present
        for port in db_ports:
            if port not in active_ports:
                not_connected += 1

        # Print to target label
        self.connected_device.setText(
            f"Running: {running} | Not Running: {not_running} | Not Connected: {not_connected}"
        )

    # -------------------- Cleanup --------------------
    def closeEvent(self, event):
        for port in list(self.threads.keys()):
            self.stop_reader(port)
        event.accept()
