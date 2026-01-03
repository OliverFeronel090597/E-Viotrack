from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QRectF


class AutoImageLabel(QLabel):
    def __init__(self, img_path, stretch=False, opacity=1.0, circle=False, size=None):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("imagelabel")

        self._pixmap = QPixmap(img_path)

        self.stretch = bool(stretch)
        self.circle = bool(circle)
        self.opacity = max(0.0, min(1.0, float(opacity)))

        # optional fixed size
        if size is not None:
            if isinstance(size, (tuple, list)) and len(size) == 2:
                self.setFixedSize(size[0], size[1])
            else:
                raise ValueError("size must be (width, height)")

    # setters
    def set_opacity(self, value: float):
        self.opacity = max(0.0, min(1.0, float(value)))
        self.update()

    def set_stretch(self, enable: bool):
        self.stretch = bool(enable)
        self.update()

    def set_circle(self, enable: bool):
        self.circle = bool(enable)
        self.update()

    def set_size(self, width: int, height: int):
        self.setFixedSize(width, height)
        self.update()

    # drawing
    def paintEvent(self, event):
        if self._pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self.opacity)

        # scale pixmap
        if self.stretch:
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        # center
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2

        if not self.circle:
            painter.drawPixmap(x, y, scaled)
        else:
            size = min(self.width(), self.height())
            circle_rect = QRectF(
                (self.width() - size) / 2,
                (self.height() - size) / 2,
                size,
                size,
            )

            path = QPainterPath()
            path.addEllipse(circle_rect)
            painter.setClipPath(path)

            painter.drawPixmap(x, y, scaled)

        painter.end()
