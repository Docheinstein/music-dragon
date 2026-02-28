from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget


class ClickableWidget(QWidget):
    clicked = pyqtSignal()

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        self.clicked.emit()