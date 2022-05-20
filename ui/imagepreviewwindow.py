from PyQt5.QtWidgets import QDialog

from log import debug
from ui.ui_imagepreviewwindow import Ui_ImagePreviewWindow


class ImagePreviewWindow(QDialog):

    def __init__(self):
        super().__init__()

        self.ui = Ui_ImagePreviewWindow()
        self.ui.setupUi(self)

    def set_image(self, pixmap):
        debug("Setting preview image")
        self.ui.image.setPixmap(pixmap)