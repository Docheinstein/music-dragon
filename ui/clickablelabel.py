from PyQt5.QtCore import pyqtSignal, QEvent, Qt
from PyQt5.QtGui import QMouseEvent, QCursor
from PyQt5.QtWidgets import QLabel


class ClickableLabel(QLabel):
    clicked = pyqtSignal(QMouseEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clickable = True
        self.underline_on_hover = False
        self.on_params_update()

    def set_clickable(self, clickable):
        self.clickable = clickable
        if not clickable:
            self.underline_on_hover = False
        self.on_params_update()

    def set_underline_on_hover(self, enabled):
        self.underline_on_hover = enabled
        self.on_params_update()

    def on_params_update(self):
        if self.clickable:
            self.setCursor(QCursor(Qt.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))

        if not self.underline_on_hover:
            f = self.font()
            f.setUnderline(False)
            self.setFont(f)

    def underline(self):
        f = self.font()
        f.setUnderline(True)
        self.setFont(f)

    def ununderline(self):
        f = self.font()
        f.setUnderline(False)
        self.setFont(f)

    def enterEvent(self, ev: QEvent) -> None:
        if self.underline_on_hover:
            self.underline()

    def leaveEvent(self, ev: QEvent) -> None:
        self.ununderline()

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if self.clickable:
            self.clicked.emit(ev)
        else:
            super().mousePressEvent(ev)