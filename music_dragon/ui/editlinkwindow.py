from PyQt5.QtWidgets import QDialog

from music_dragon.ui.ui_editlinkwindow import Ui_EditLinkWindow

class EditLinkWindow(QDialog):

    def __init__(self, link: str=None):
        super().__init__()

        self.image = None
        self.ui = Ui_EditLinkWindow()
        self.ui.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self.link = link
        if link:
            self.ui.link.setText(self.link)


    def accept(self) -> None:
        super(EditLinkWindow, self).accept()
        self.link = self.ui.link.text()
