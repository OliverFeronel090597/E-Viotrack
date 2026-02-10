import serial
import re
from PyQt6.QtCore import pyqtSignal, QObject


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
            except Exception as e:
                print(f"[{self.port}] Serial error:", e)
                break

            if line:
                tag = line.decode(errors="ignore").strip()
                if tag:
                    tag = self.get_int_signed(tag)  # this returns int
                    if tag is not None:
                        self.tag_signal.emit(self.port, str(tag))   # FIX: must be string
                    else:
                        self.tag_signal.emit(self.port, "")         # or ignore

        self.stop()
        self.finished.emit(self.port)
        print(f"[{self.port}] Worker stopped")

    def get_int_signed(self, s: str):
        m = re.search(r"[+-]?\d+", s)
        return int(m.group()) if m else None
