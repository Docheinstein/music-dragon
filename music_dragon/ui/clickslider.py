from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QSlider

from music_dragon.log import debug


class ClickSlider(QSlider):

    def __init__(self, parent):
        super().__init__(parent)

    def mouseReleaseEvent(self, e: QMouseEvent):
        e.accept()
        x = e.pos().x()
        value = int((self.maximum() - self.minimum()) * x / self.width() + self.minimum())
        self.set_value(value, notify=True)

    def set_value(self, value: int, notify: bool=True):
        debug(f"set_value({value})")
        if self.value() == value:
            return
        was_blocked = False
        if not notify:
            was_blocked = self.blockSignals(True)
        self.setValue(value)
        if not notify:
            self.blockSignals(was_blocked)

