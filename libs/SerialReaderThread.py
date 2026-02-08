from PyQt6.QtCore import QThread, pyqtSignal
import serial


# ---------------- SERIAL READER THREAD ----------------
class SerialReaderThread(QThread):
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port: str, baudrate: int = None, parent=None):
        super().__init__(parent)
        self.port_name = port
        self.baudrate = baudrate
        self.running = True
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.port_name, self.baudrate, timeout=1)
        except serial.SerialException as e:
            self.error_occurred.emit(f"Cannot open port {self.port_name}: {e}")
            return

        while self.running:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode(errors="ignore").strip()
                    if line:
                        self.data_received.emit(line)
                if not self.ser.is_open:
                    self.error_occurred.emit(f"Port {self.port_name} disconnected")
                    break
            except serial.SerialException as e:
                self.error_occurred.emit(f"Serial error on {self.port_name}: {e}")
                break
            except Exception as e:
                print(f"Unknown error: {e}")

        if self.ser and self.ser.is_open:
            self.ser.close()

    def stop(self):
        self.running = False
        self.quit()
        self.wait()
