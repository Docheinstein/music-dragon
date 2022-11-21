from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QSlider


class ClickSlider(QSlider):
    valueChangedManually = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.pressing = False
        self.moving = False

    def mousePressEvent(self, e: QMouseEvent) -> None:
        self.pressing = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self.pressing = False

        if self.orientation() == QtCore.Qt.Horizontal:
            x = e.pos().x()
            value = int(self.minimum() + (x / self.width()) * (self.maximum() - self.minimum()))
        else:
            y = e.pos().y()
            value = int(self.minimum() + (1 - (y / self.height())) * (self.maximum() - self.minimum()))

        self.set_value(value, notify=True)

        super().mouseReleaseEvent(e)

    def set_value(self, value: int, notify: bool = False):
        if self.pressing:
            return
        if self.value() == value:
            return
        self.setValue(value)
        if notify:
            self.valueChangedManually.emit(value)