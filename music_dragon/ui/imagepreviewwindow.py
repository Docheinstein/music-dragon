from pathlib import Path

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

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
        if image:
            self.image = image
            self.ui.image.setPixmap(make_pixmap_from_data(image))
        else:
            print("WARN: no image to show")

    def _on_save_button_clicked(self):
        directory_picker = QFileDialog()

        result = directory_picker.getSaveFileName(self, "Save file", "", "")
        if result:
            filename = result[0]
            debug(f"Selected file: {filename}")

            try:
                with Path(filename).open("wb") as f:
                    f.write(self.image)
                QMessageBox.information(self, "Saved",
                                     "Image has been saved successfully",
                                     QMessageBox.Ok)
                self.close()
            except:
                print(f"WARN: failed to save image to {filename}")
                QMessageBox.critical(self, "Save failed",
                                     "Failed to save image to",
                                     QMessageBox.Ok)

