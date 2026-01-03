from PyQt6.QtWidgets import  QStackedWidget

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

# -------------------- ANIMATED STACK --------------------
class AnimatedStack(QStackedWidget):
    def __init__(self, duration=250):
        super().__init__()
        self.duration = duration
        self._anim_out = None
        self._anim_in = None

    def slide_to(self, index: int):
        if index == self.currentIndex():
            return

        direction = 1 if index > self.currentIndex() else -1

        current = self.currentWidget()
        target = self.widget(index)

        target.setGeometry(current.geometry().translated(direction * self.width(), 0))
        self.setCurrentWidget(target)

        anim_out = QPropertyAnimation(current, b"geometry")
        anim_out.setDuration(self.duration)
        anim_out.setEndValue(current.geometry().translated(-direction * self.width(), 0))

        anim_in = QPropertyAnimation(target, b"geometry")
        anim_in.setDuration(self.duration)
        anim_in.setEndValue(current.geometry())

        for anim in (anim_in, anim_out):
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim.start()

        self._anim_out = anim_out
        self._anim_in = anim_in
