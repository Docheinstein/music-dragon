from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDialog, QFileDialog

from log import debug
import preferences
from ui.ui_preferenceswindow import Ui_PreferencesWindow


class PreferencesWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.ui = Ui_PreferencesWindow()
        self.ui.setupUi(self)


        self.ui.downloadDirectoryWidget.clicked.connect(self.on_download_directory_clicked)

        # OK / CANCEL
        self.accepted.connect(self.on_accepted)
        self.rejected.connect(self.on_rejected)

        # Actually load settings
        self.load_settings()

    def on_accepted(self):
        debug("Saving preferences")
        self.save_settings()

    def on_rejected(self):
        debug("Closing preferences window without saving")

    def on_download_directory_clicked(self):
        debug("Opening download directory picker")
        download_directory_picker = QFileDialog()
        download_directory_picker.setFileMode(QFileDialog.Directory)
        if download_directory_picker.exec():
            results = download_directory_picker.selectedFiles()
            if not results:
                print("WARN: no download directory has been selected")
                return

            result = results[0]
            debug(f"Selected download directory: {result}")
            self.ui.downloadDirectory.setText(result)


    def load_settings(self):
        self.ui.downloadDirectory.setText(preferences.download_directory())

    def save_settings(self):
        preferences.set_download_directory(self.ui.downloadDirectory.text())
