from PyQt5 import QtCore
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QSlider


class ClickSlider(QSlider):
    def __init__(self, parent):
        super().__init__(parent)
        self.pressing = False
        self.moving = False
        # self.setTracking(False)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        print("mousePressEvent")
        self.pressing = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        print("mouseReleaseEvent")
        self.pressing = False

        if not self.moving:
            e.accept()
            if self.orientation() == QtCore.Qt.Horizontal:
                x = e.pos().x()
                value = int(self.minimum() + (x / self.width()) * (self.maximum() - self.minimum()))
            else:
                y = e.pos().y()
                value = int(self.minimum() + (1 - (y / self.height())) * (self.maximum() - self.minimum()))
            self.set_value(value, notify=True)
        else:
            super().mouseReleaseEvent(e)

        self.moving = False

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        print("mouseMoveEvent")
        super().mouseMoveEvent(e)
        self.moving = True


    def set_value(self, value: int, notify: bool=True):
        if self.pressing:
            return
        if self.value() == value:
            return
        print(f"set_value={value}")
        was_blocked = False
        if not notify:
            was_blocked = self.blockSignals(True)
        self.setValue(value)
        if not notify:
            self.blockSignals(was_blocked)

