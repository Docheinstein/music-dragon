from pathlib import Path

from PyQt5.QtWidgets import QDialog, QFileDialog

from music_dragon import cache, preferences
from music_dragon.log import debug
from music_dragon.ui.ui_preferenceswindow import Ui_PreferencesWindow
from music_dragon.utils import open_folder, app_cache_path


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
        self.ui.directory.clicked.connect(self.on_directory_clicked)
        self.ui.browseDirectoryButton.clicked.connect(self.on_browse_directory_button_clicked)

        # Cache
        self.ui.cache.clicked.connect(self.on_cache_clicked)
        self.ui.cacheClearButton.clicked.connect(self.on_clear_cache_button_clicked)
        self.update_cache_size()

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
        self.ui.cacheImagesCheck.setChecked(preferences.is_images_cache_enabled())
        self.ui.cacheRequestsBox.setChecked(preferences.is_requests_cache_enabled())
        self.ui.cache.setText(str(app_cache_path().absolute()))

    def save_settings(self):
        preferences.set_directory(self.ui.directory.text())
        preferences.set_cover_size(PreferencesWindow.COVER_SIZE_VALUES[self.ui.coverSize.currentIndex()])
        preferences.set_output_format(self.ui.outputFormat.text())
        preferences.set_thread_number(self.ui.threadNumber.value())
        preferences.set_max_simultaneous_downloads(self.ui.maxSimultaneousDownloads.value())
        preferences.set_images_cache_enabled(self.ui.cacheImagesCheck.isChecked())
        preferences.set_requests_cache_enabled(self.ui.cacheRequestsBox.isChecked())

        cache.enable_images_cache(preferences.is_images_cache_enabled())
        cache.enable_requests_cache(preferences.is_requests_cache_enabled())

    def on_directory_clicked(self):
        directory_str = self.ui.directory.text()
        debug(f"Opening directory: {directory_str}")
        directory = Path(directory_str)
        if not directory.exists():
            print(f"WARN: cannot open directory: '{directory_str}' does not exist")
            return
        open_folder(directory)

    def on_browse_directory_button_clicked(self):
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


    def on_cache_clicked(self):
        open_folder(app_cache_path())

    def on_clear_cache_button_clicked(self):
        cache.clear()
        self.update_cache_size()

    def update_cache_size(self):
        self.ui.cacheSize.setText(f"Size: {int(cache.cache_size() / 2**20)}MB")
