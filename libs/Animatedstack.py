import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFontDatabase, QFont

class SevenSegmentClock(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("7-Segment Clock")

        # Load 7-segment TTF font (place the font file in 'fonts/' folder)
        font_id = QFontDatabase.addApplicationFont("fonts/Digital-7.ttf")
        if font_id == -1:
            print("Failed to load 7-segment font.")
            sys.exit(1)
        family = QFontDatabase.applicationFontFamilies(font_id)[0]

        # Create label for clock
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Apply 7-segment font with spacing
        font = QFont(family, 60)  # font size
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10)  # spacing between digits
        self.label.setFont(font)

        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Timer updates every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.update_time()

    def update_time(self):
        now = QTime.currentTime()
        # Insert spaces around colons for extra spacing
        time_str = now.toString("hh : mm : ss")
        self.label.setText(time_str)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock = SevenSegmentClock()
    clock.resize(600, 150)
    clock.show()
    sys.exit(app.exec())
