from PyQt5.QtWidgets import QDialog

from music_dragon import ytdownloader, preferences
from music_dragon.log import debug
from music_dragon.ui.ui_youtubesigninwindow import Ui_YouTubeSignInWindow


class YouTubeSignInWindow(QDialog):

    def __init__(self):
        super().__init__()

        self.ui = Ui_YouTubeSignInWindow()
        self.ui.setupUi(self)

        # OK / CANCEL
        self.accepted.connect(self.on_accepted)
        self.rejected.connect(self.on_rejected)

    def on_accepted(self):
        debug("Saving youtube credentials")
        email = self.ui.email.text()
        password = self.ui.password.text()
        ytdownloader.sign_in(email, password)

        if self.ui.rememberMe.isChecked():
            preferences.set_youtube_email(email)
            preferences.set_youtube_email(password)


    def on_rejected(self):
        pass

