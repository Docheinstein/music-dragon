from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox

from music_dragon import ytmusic
from music_dragon.log import debug
from music_dragon.ui.ui_ytmusicsetupwindow import Ui_YtMusicSetupWindow


class YtMusicSetupWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.ui = Ui_YtMusicSetupWindow()
        self.ui.setupUi(self)

        self.error = None

        self.ui.buttons.button(QDialogButtonBox.Ok).setText("Setup")

        self.accepted.connect(self.on_accepted)
        self.rejected.connect(self.on_rejected)

        self.ui.pasteArea.textChanged.connect(self.on_text_changed)

        self.update_buttons()


    def on_accepted(self):
        debug("Going to create ytmusicapi auth file")
        headers = self.ui.pasteArea.toPlainText()
        try:
            ytmusic.create_auth_file(headers)
            self.error = None
        except Exception as e:
            print(f"ERROR: failed to create ytmusic api auth file: {e}")
            self.error = str(e)

    def on_rejected(self):
        debug("Closing ytmusicsetup")

    def on_text_changed(self):
        self.update_buttons()

    def update_buttons(self):
        text = self.ui.pasteArea.toPlainText()
        self.ui.buttons.button(QDialogButtonBox.Ok).setEnabled(True if text else False)

    def accept(self) -> None:
        if self.error:
            self.show_warning()
        else:
            try:
                ytmusic.initialize()
                super().accept()
            except Exception as e:
                print(f"ERROR: failed to initialize ytmusic api auth file: {e}")
                self.error = str(e)
                self.show_warning()

    def show_warning(self):
        QMessageBox.critical(self, "YtMusic Setup Failed",
                             "Failed to create YtMusic API auth file.\n"
                             f"{self.error}",
                             QMessageBox.Ok)

    def reject(self) -> None:
        QMessageBox.warning(self, "YtMusic Setup Failed",
                            "You won't be able to use YtMusic API if you don't configure it!",
                            QMessageBox.Ok)
        super().reject()