import re
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QIODevice
from PyQt6.QtSerialPort import QSerialPort

class RFIDWorker(QObject):
    tag_signal = pyqtSignal(str, str)  # port, tag
    finished = pyqtSignal(str)         # port

    def __init__(self, port: str, baud: int):
        super().__init__()
        self.port = port
        self.baud = baud
        self.running = True
        self.buffer = bytearray()
        self.serial = None
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.run)
        self.thread.finished.connect(self.thread.deleteLater)

    def start(self):
        self.thread.start()
        print(f"[{self.port}] Worker thread started @ {self.baud}")

    def stop(self):
        self.running = False
        if self.serial and self.serial.isOpen():
            self.serial.close()
        self.finished.emit(self.port)
        self.thread.quit()
        self.thread.wait()
        print(f"[{self.port}] Worker stopped")

    def run(self):
        # create serial port inside this thread context
        self.serial = QSerialPort()
        self.serial.setPortName(self.port)
        self.serial.setBaudRate(self.baud)
        self.serial.readyRead.connect(self.handle_ready_read)

        if not self.serial.open(QIODevice.OpenModeFlag.ReadWrite):
            print(f"[{self.port}] Cannot open")
            self.finished.emit(self.port)
            return

        print(f"[{self.port}] Serial opened")

    def handle_ready_read(self):
        if not self.running:
            return

        data = self.serial.readAll()
        self.buffer.extend(data)

        while b'\n' in self.buffer:
            line, sep, remaining = self.buffer.partition(b'\n')
            self.buffer = remaining
            tag_str = line.decode(errors='ignore').strip()
            if tag_str:
                tag_int = self.get_int_signed(tag_str)
                self.tag_signal.emit(self.port, str(tag_int) if tag_int is not None else "")

    def get_int_signed(self, s: str):
        m = re.search(r"[+-]?\d+", s)
        return int(m.group()) if m else None
