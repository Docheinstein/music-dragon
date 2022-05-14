from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QListView


class ClickableListView(QListView):
    pass
    # mouse_pressed = pyqtSignal(QMouseEvent)
    #
    # def mousePressEvent(self, ev: QMouseEvent) -> None:
    #     self.mouse_pressed.emit(ev)