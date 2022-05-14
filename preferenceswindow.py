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


        self.ui.directoryWidget.clicked.connect(self.on_download_directory_clicked)

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
        directory_picker = QFileDialog()
        directory_picker.setFileMode(QFileDialog.Directory)
        if directory_picker.exec():
            results = directory_picker.selectedFiles()
            if not results:
                print("WARN: no directory has been selected")
                return

            result = results[0]
            debug(f"Selected directory: {result}")
            self.ui.directory.setText(result)


    def load_settings(self):
        self.ui.directory.setText(preferences.directory())

    def save_settings(self):
        preferences.set_directory(self.ui.directory.text())
