import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox,
    QListWidget, QHBoxLayout, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QThread
from libs.DatabaseConnector import DatabaseConnector

BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400]


# ===================== RFID Worker =====================
class RFIDWorker(QObject):
    tag_signal = pyqtSignal(str, str)  # port, tag
    finished = pyqtSignal(str)         # port

    def __init__(self, port: str, baud: int):
        super().__init__()
        self.port = port
        self.baud = baud
        self.running = True
        self.ser = None

    def stop(self):
        self.running = False
        if self.ser:
            try:
                if self.ser.is_open:
                    self.ser.close()
            except Exception as e:
                print(f"[{self.port}] Serial close failed: {e}")
            finally:
                self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.3)
        except Exception as e:
            print(f"[{self.port}] Cannot open:", e)
            self.finished.emit(self.port)
            return

        while self.running:
            try:
                line = self.ser.readline()
            except Exception:
                break

            if line:
                tag = line.decode(errors="ignore").strip()
                if tag:
                    self.tag_signal.emit(self.port, tag)

        self.stop()
        self.finished.emit(self.port)
        print(f"[{self.port}] Worker stopped")


# ===================== RFID Manager =====================
class RFIDManager(QWidget):
    POLL_INTERVAL_MS = 2000
    MAX_TAG_LINES_DEFAULT = 1000  # fixed default

    def __init__(self, upfdate_rfid, db: DatabaseConnector):
        super().__init__()
        self.setWindowTitle("Multi-RFID Manager")
        self.resize(600, 450)

        self.db = db
        self.upfdate_rfid = upfdate_rfid

        self.threads = {}    # port -> QThread
        self.workers = {}    # port -> RFIDWorker
        self.checkboxes = {} # port -> QCheckBox
        self.combos = {}     # port -> QComboBox
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

        self.tag_list = QListWidget()
        self.tag_list.setObjectName("rfidTagList")
        layout.addWidget(self.tag_list)

        # --- Auto scan timer ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_ports)
        self.timer.start(self.POLL_INTERVAL_MS)

        self.check_ports()  # initial scan

    # -------------------- Port scan --------------------
    def check_ports(self):
        available = {p.device for p in serial.tools.list_ports.comports()}

        for port in available - self.current_ports:
            self.add_port_widget(port)
        for port in self.current_ports - available:
            self.remove_port_widget(port)

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
        if port in self.threads:
            return
        worker = RFIDWorker(port, baud)
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.tag_signal.connect(self.on_tag_read)
        worker.finished.connect(self.on_worker_finished)
        self.threads[port] = thread
        self.workers[port] = worker
        thread.start()
        print(f"[{port}] QThread started @ {baud}")

    def stop_reader(self, port):
        if port not in self.threads:
            return
        worker = self.workers.pop(port, None)
        thread = self.threads.pop(port, None)
        if worker:
            worker.stop()
        if thread:
            thread.quit()
            thread.wait(500)
        print(f"[{port}] QThread stopped")

    def on_worker_finished(self, port):
        print(f"[{port}] Worker exit")
        self.workers.pop(port, None)
        self.threads.pop(port, None)

    # -------------------- Tag display --------------------
    def on_tag_read(self, port, tag):
        self.tag_list.addItem(f"{port} → {tag}")
        max_lines = self.MAX_TAG_LINES_DEFAULT
        while self.tag_list.count() > max_lines:
            self.tag_list.takeItem(0)
        self.tag_list.scrollToBottom()
        try:
            if hasattr(self.upfdate_rfid, "handle_add_violation"):
                self.upfdate_rfid.handle_add_violation(tag)
        except Exception as e:
            print("RFID process error:", e)

    # -------------------- Cleanup --------------------
    def closeEvent(self, event):
        for port in list(self.threads.keys()):
            self.stop_reader(port)
        event.accept()
