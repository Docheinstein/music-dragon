from pathlib import Path

from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox

from music_dragon import cache, preferences, ytdownloader
from music_dragon.log import debug
from music_dragon.ui.ui_preferenceswindow import Ui_PreferencesWindow
from music_dragon.utils import open_folder, app_cache_path


class PreferencesWindow(QDialog):
    COVER_SIZES = [250, 500, 1200, None]

    YT_COOKIES_FROM_BROWSER = ['', 'chrome', 'firefox', 'brave', 'edge', 'chromium', 'opera']
    YT_JS_CHALLENGES_SOLVERS = ['deno', 'node']

    def __init__(self):
        super().__init__()

        self.ui = Ui_PreferencesWindow()
        self.ui.setupUi(self)

        # Directory
        self.ui.directory.clicked.connect(self.on_directory_clicked)
        self.ui.browseDirectoryButton.clicked.connect(self.on_browse_directory_button_clicked)

        # Download directory
        self.ui.manualDownloadDirectory.clicked.connect(self.on_manual_download_directory_clicked)
        self.ui.browseManualDownloadDirectoryButton.clicked.connect(
            self.on_browse_manual_download_directory_button_clicked)

        # Cache
        self.ui.cache.clicked.connect(self.on_cache_clicked)
        self.ui.cacheClearButton.clicked.connect(self.on_clear_cache_button_clicked)
        self.update_cache_size()

        # YouTube
        self.ui.testYoutubeCookiesFromBrowserButton.clicked.connect(self.on_test_youtube_cookies_from_browser_button_clicked)
        self.ui.browseYoutubeChallengesSolverButton.clicked.connect(self.on_browse_youtube_challenges_solver_button_clicked)
        self.ui.clearYoutubeChallengesSolverButton.clicked.connect(self.on_clear_youtube_challenges_solver_button_clicked)

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
        self.ui.manualDownloadDirectory.setText(preferences.manual_download_directory())
        self.ui.coverSize.setCurrentIndex(PreferencesWindow.COVER_SIZES.index(preferences.cover_size()))
        self.ui.outputFormat.setText(preferences.output_format())
        self.ui.manualOutputFormat.setText(preferences.manual_output_format())
        self.ui.threadNumber.setValue(preferences.thread_number())
        self.ui.maxSimultaneousDownloads.setValue(preferences.max_simultaneous_downloads())
        self.ui.cacheImagesCheck.setChecked(preferences.is_images_cache_enabled())
        self.ui.cacheRequestsBox.setChecked(preferences.is_requests_cache_enabled())
        self.ui.cacheLocalSongs.setChecked(preferences.is_localsongs_cache_enabled())
        self.ui.cache.setText(str(app_cache_path().absolute()))
        self.ui.youtubeCookiesFromBrowserCombo.setCurrentIndex(
            PreferencesWindow.YT_COOKIES_FROM_BROWSER.index(preferences.get_youtube_cookies_from_browser()))
        self.ui.youtubeChallengesSolverCombo.setCurrentIndex(
            PreferencesWindow.YT_JS_CHALLENGES_SOLVERS.index(preferences.get_youtube_js_challenges_solver()))
        self.ui.youtubeChallengesSolver.setText(preferences.get_youtube_js_challenges_solver_path())

    def save_settings(self):
        preferences.set_directory(self.ui.directory.text())
        preferences.set_manual_download_directory(self.ui.manualDownloadDirectory.text())
        preferences.set_cover_size(PreferencesWindow.COVER_SIZES[self.ui.coverSize.currentIndex()])
        preferences.set_output_format(self.ui.outputFormat.text())
        preferences.set_manual_output_format(self.ui.manualOutputFormat.text())
        preferences.set_thread_number(self.ui.threadNumber.value())
        preferences.set_max_simultaneous_downloads(self.ui.maxSimultaneousDownloads.value())

        preferences.set_images_cache_enabled(self.ui.cacheImagesCheck.isChecked())
        preferences.set_requests_cache_enabled(self.ui.cacheRequestsBox.isChecked())
        preferences.set_localsongs_cache_enabled(self.ui.cacheLocalSongs.isChecked())

        cache.enable_images_cache(preferences.is_images_cache_enabled())
        cache.enable_requests_cache(preferences.is_requests_cache_enabled())
        cache.enable_localsongs_cache(preferences.is_localsongs_cache_enabled())

        preferences.set_youtube_cookies_from_browser(
            PreferencesWindow.YT_COOKIES_FROM_BROWSER[self.ui.youtubeCookiesFromBrowserCombo.currentIndex()])
        preferences.set_youtube_js_challenges_solver(
            PreferencesWindow.YT_JS_CHALLENGES_SOLVERS[self.ui.youtubeChallengesSolverCombo.currentIndex()])
        preferences.set_youtube_js_challenges_solver_path(self.ui.youtubeChallengesSolver.text())


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
        directory_picker.setFileMode(QFileDialog.FileMode.Directory)
        if directory_picker.exec():
            results = directory_picker.selectedFiles()
            if not results:
                print("WARN: no directory has been selected")
                return

            result = results[0]
            debug(f"Selected directory: {result}")
            self.ui.directory.setText(result)

    def on_manual_download_directory_clicked(self):
        directory_str = self.ui.manualDownloadDirectory.text()
        debug(f"Opening download_directory: {directory_str}")
        directory = Path(directory_str)
        if not directory.exists():
            print(f"WARN: cannot open directory: '{directory_str}' does not exist")
            return
        open_folder(directory)

    def on_browse_manual_download_directory_button_clicked(self):
        debug("Opening download directory picker")
        directory_picker = QFileDialog()
        directory_picker.setFileMode(QFileDialog.FileMode.Directory)
        if directory_picker.exec():
            results = directory_picker.selectedFiles()
            if not results:
                print("WARN: no directory has been selected")
                return

            result = results[0]
            debug(f"Selected directory: {result}")
            self.ui.manualDownloadDirectory.setText(result)

    def on_test_youtube_cookies_from_browser_button_clicked(self):
        idx = self.ui.youtubeCookiesFromBrowserCombo.currentIndex()
        browser = self.YT_COOKIES_FROM_BROWSER[idx]
        if not browser:
            QMessageBox.information(self, "Test cookies", "No browser selected.")
            return

        try:
            import yt_dlp.cookies as yt_cookies
            jar = yt_cookies.extract_cookies_from_browser(browser)
            yt_count = sum(1 for c in jar if 'youtube.com' in c.domain or 'google.com' in c.domain)
            total_count = sum(1 for _ in jar)

            if yt_count > 0:
                QMessageBox.information(
                    self, "Test cookies",
                    f"Found {yt_count} YouTube/Google cookies in browser '{browser}'.\n\n"
                    "Everything seems fine!"
                )
            else:
                QMessageBox.warning(
                    self, "Test cookies",
                    f"No YouTube/Google cookies found in browser '{browser}'.\n\n"
                    "Make sure you are logged into YouTube."
                )
        except Exception as e:
            QMessageBox.critical(self, "Test cookies", f"Failed to read cookies from {browser}:\n\n{e}")

    def on_browse_youtube_challenges_solver_button_clicked(self):
        debug("Opening YouTube JS challenges file picker")
        directory_picker = QFileDialog()
        directory_picker.setFileMode(QFileDialog.FileMode.ExistingFile)
        if directory_picker.exec():
            results = directory_picker.selectedFiles()
            if not results:
                print("WARN: no file has been selected")
                return

            result = results[0]
            debug(f"Selected JS challenges solver path: {result}")
            self.ui.youtubeChallengesSolver.setText(result)

    def on_clear_youtube_challenges_solver_button_clicked(self):
        debug("Clearing YouTube JS challenges path")
        self.ui.youtubeChallengesSolver.setText("")

    def on_cache_clicked(self):
        open_folder(app_cache_path())

    def on_clear_cache_button_clicked(self):
        cache.clear()
        self.update_cache_size()

    def update_cache_size(self):
        self.ui.cacheSize.setText(f"Size: {int(cache.cache_size() / 2 ** 20)}MB")
