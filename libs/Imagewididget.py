from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import Qt

from libs.DatabaseConnector import DatabaseConnector


class HomePage(QWidget):
    def __init__(self, db: DatabaseConnector, img_path, stretch=False, opacity=1.0):
        super().__init__()
        self._pixmap = QPixmap(img_path)

        # settings
        self.stretch = stretch          # True = fill widget, no aspect ratio
        self.opacity = float(opacity)   # 0.0–1.0

        if self.opacity < 0: self.opacity = 0
        if self.opacity > 1: self.opacity = 1

        












    def set_opacity(self, value: float):
        self.opacity = max(0.0, min(1.0, float(value)))
        self.update()

    def set_stretch(self, enable: bool):
        self.stretch = bool(enable)
        self.update()

    def paintEvent(self, event):
        if self._pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setOpacity(self.opacity)

        if self.stretch:
            # Fill full widget, ignore aspect ratio
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)

        else:
            # Keep aspect ratio and center it
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        painter.end()
