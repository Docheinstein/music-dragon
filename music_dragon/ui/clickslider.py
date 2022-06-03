from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QSlider


class ClickSlider(QSlider):

    def __init__(self, parent):
        super().__init__(parent)

    def mouseReleaseEvent(self, e: QMouseEvent):
        e.accept()
        x = e.pos().x()
        value = int((self.maximum() - self.minimum()) * x / self.width() + self.minimum())
        self.setValue(value, notify=True)

    def setValue(self, value: int, notify: bool=True):
        was_blocked = False
        if not notify:
            was_blocked = self.blockSignals(True)
        super().setValue(value)
        if not notify:
            self.blockSignals(was_blocked)
