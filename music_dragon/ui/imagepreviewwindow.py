from pathlib import Path

from PyQt5.QtWidgets import QDialog, QFileDialog

from music_dragon.log import debug
from music_dragon.ui.ui_imagepreviewwindow import Ui_ImagePreviewWindow
from music_dragon.utils import make_pixmap_from_data


class ImagePreviewWindow(QDialog):

    def __init__(self):
        super().__init__()

        self.image = None
        self.ui = Ui_ImagePreviewWindow()
        self.ui.setupUi(self)

        self.ui.saveButton.clicked.connect(self._on_save_button_clicked)

    def set_image(self, image: bytes):
        debug("Setting preview image")
        self.image = image
        self.ui.image.setPixmap(make_pixmap_from_data(image))

    def _on_save_button_clicked(self):
        directory_picker = QFileDialog()
        directory_picker.setFileMode(QFileDialog.AnyFile)
        if directory_picker.exec():
            results = directory_picker.selectedFiles()
            if not results:
                print("WARN: no directory has been selected")
                return

            result = results[0]
            debug(f"Selected file: {result}")

            try:
                with Path(result).open("w") as f:
                    f.write(self.image)
            except:
                print("WARN: failed to save image")


