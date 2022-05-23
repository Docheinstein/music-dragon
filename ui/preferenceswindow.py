from pathlib import Path

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog, QFileDialog

from log import debug
import preferences
from ui.ui_preferenceswindow import Ui_PreferencesWindow


class PreferencesWindow(QDialog):
    COVER_SIZE_VALUES = [
        250,
        500,
        1200,
        None
    ]
    COVER_SIZE_INDEXES = {
        250: 0,
        500: 1,
        1200: 2,
        None: 3
    }

    def __init__(self):
        super().__init__()

        self.ui = Ui_PreferencesWindow()
        self.ui.setupUi(self)

        # Directory
        self.ui.directoryWidget.clicked.connect(self.on_download_directory_clicked)
        self.ui.openDirectoryButton.clicked.connect(self.on_open_directory_button_clicked)

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

    def load_settings(self):
        self.ui.directory.setText(preferences.directory())
        self.ui.coverSize.setCurrentIndex(PreferencesWindow.COVER_SIZE_INDEXES[preferences.cover_size()])
        self.ui.outputFormat.setText(preferences.output_format())
        self.ui.threadNumber.setValue(preferences.thread_number())
        self.ui.maxSimultaneousDownloads.setValue(preferences.max_simultaneous_downloads())

    def save_settings(self):
        preferences.set_directory(self.ui.directory.text())
        preferences.set_cover_size(PreferencesWindow.COVER_SIZE_VALUES[self.ui.coverSize.currentIndex()])
        preferences.set_output_format(self.ui.outputFormat.text())
        preferences.set_thread_number(self.ui.threadNumber.value())
        preferences.set_max_simultaneous_downloads(self.ui.maxSimultaneousDownloads.value())


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

    def on_open_directory_button_clicked(self):
        directory_str = self.ui.directory.text()
        debug(f"Opening directory: {directory_str}")
        directory = Path(directory_str)
        if not directory.exists():
            print(f"WARN: cannot open directory: '{directory_str}' does not exist")
            return
        # debug(f"abs: {str(directory.absolute())}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory.absolute())))
        # QDesktopServices.openUrl(QUrl(f"file://{str(directory.absolute())}"))