from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QWidget


class ClickableWidget(QWidget):
    clicked = pyqtSignal()

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        self.clicked.emit()