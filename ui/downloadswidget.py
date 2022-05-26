from typing import List, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QGridLayout, QProgressBar, QPushButton, QVBoxLayout, \
    QSpacerItem, QListWidgetItem

import ui
import ytdownloader
from log import debug
from repository import get_track, Track, get_youtube_track
from ui.clickablelabel import ClickableLabel
from ui.listwidgetmodelview import ListWidgetModelView, ListWidgetModelViewItem, ListWidgetModel
from utils import make_pixmap_from_data


class DownloadsItemWidget(ListWidgetModelViewItem):
    artist_clicked = pyqtSignal(str)
    album_clicked = pyqtSignal(str)
    cancel_button_clicked = pyqtSignal(str)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.artist: Optional[QLabel] = None
            self.album: Optional[QLabel] = None
            self.download_progress: Optional[QProgressBar] = None
            self.download_error: Optional[QLabel] = None
            self.cancel_button: Optional[QPushButton] = None

    def __init__(self, track_id: str):
        super().__init__(entry=track_id)

        self.track_id = track_id
        self.track: Track = get_track(self.track_id)
        if not self.track:
            print(f"WARN: no track for id '{self.track_id}'")
            return

        self.ui = DownloadsItemWidget.Ui()
        self.setup()
        self.invalidate()


    def setup(self):
        # cover
        self.ui.cover = QLabel()
        self.ui.cover.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ui.cover.setMaximumSize(QSize(64, 64))
        self.ui.cover.setScaledContents(True)

        # title
        self.ui.title = QLabel()
        self.ui.title.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        # artist
        self.ui.artist = ClickableLabel()
        self.ui.artist.set_underline_on_hover(True)
        f = self.ui.artist.font()
        f.setPointSize(10)
        self.ui.artist.setFont(f)
        self.ui.artist.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ui.artist.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.ui.artist.clicked.connect(self._on_artist_clicked)

        # -
        dash = QLabel(" - ")
        f = dash.font()
        f.setPointSize(10)
        dash.setFont(f)
        dash.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        dash.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # album
        self.ui.album = ClickableLabel()
        self.ui.album.set_underline_on_hover(True)
        f = self.ui.album.font()
        f.setPointSize(10)
        self.ui.album.setFont(f)
        self.ui.album.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ui.album.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.ui.album.clicked.connect(self._on_album_clicked)

        # download progress
        self.ui.download_progress = QProgressBar()
        self.ui.download_progress.setMaximumHeight(8)
        self.ui.download_progress.setTextVisible(False)
        self.ui.download_progress.setMinimum(0)
        self.ui.download_progress.setMaximum(100)
        self.ui.download_progress.setOrientation(Qt.Horizontal)
        self.ui.download_progress.setValue(0)

        # download errors
        self.ui.download_error = QLabel()
        self.ui.download_error.setStyleSheet("QLabel { color: red; }")
        self.ui.download_error.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.ui.download_error.setVisible(False)

        # cancel button
        self.ui.cancel_button = QPushButton()
        self.ui.cancel_button.setVisible(False)
        self.ui.cancel_button.setIcon(ui.resources.X_ICON)
        self.ui.cancel_button.setFlat(True)
        self.ui.cancel_button.setCursor(Qt.PointingHandCursor)
        self.ui.cancel_button.setIconSize(QSize(24, 24))
        self.ui.cancel_button.clicked.connect(self._on_cancel_button_clicked)

        # build
        outer_layout = QHBoxLayout()
        outer_layout.setSpacing(4)
        outer_layout.addWidget(self.ui.cover)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)

        subtitle_layout = QHBoxLayout()
        subtitle_layout.addWidget(self.ui.artist)
        subtitle_layout.addWidget(dash)
        subtitle_layout.addWidget(self.ui.album)
        subtitle_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        content_layout.addWidget(self.ui.title)
        content_layout.addLayout(subtitle_layout)

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(8, 0, 0, 0)

        grid_layout.addLayout(content_layout, 0, 0)
        grid_layout.addWidget(self.ui.download_progress, 0, 0, alignment=Qt.AlignBottom)
        grid_layout.addWidget(self.ui.download_error, 0, 0, alignment=Qt.AlignBottom)

        outer_layout.addLayout(grid_layout)
        outer_layout.addWidget(self.ui.cancel_button)

        self.setLayout(outer_layout)

    def invalidate(self):
        if self.track_id is None:
            return

        self.track = get_track(self.track_id)
        release_group = self.track.release().release_group()

        # cover
        cover = release_group.images.preferred_image()
        self.ui.cover.setPixmap(make_pixmap_from_data(cover, default=ui.resources.COVER_PLACEHOLDER_PIXMAP))

        # title
        self.ui.title.setText(self.track.title)

        # artist
        self.ui.artist.setText(self.track.release().release_group().artists_string())

        # album
        self.ui.album.setText(self.track.release().release_group().title)

        # progress
        youtube_track = get_youtube_track(self.track.youtube_track_id)
        download = ytdownloader.get_download(youtube_track.video_id)
        if not download:
            download = ytdownloader.get_finished_download(youtube_track.video_id)

        # error
        if download:
            if download["status"] == "queued":
                self.ui.download_progress.setVisible(False)
                self.ui.download_error.setVisible(False)
                self.ui.cancel_button.setVisible(True)
            elif download["status"] == "downloading":
                self.ui.download_progress.setVisible(True)
                self.ui.download_progress.setValue(round(download["progress"]))
                self.ui.download_error.setVisible(False)
                self.ui.cancel_button.setVisible(True) # TODO: handle this
            elif download["status"] == "finished":
                self.ui.download_progress.setVisible(False)
                self.ui.cancel_button.setVisible(False)

                if "error" in download:
                    self.ui.download_error.setVisible(True)
                    self.ui.download_error.setText(download["error"])
                else:
                    self.ui.download_error.setVisible(False)
            else:
                print(f"WARN: unknown status: {download['status']}")
        else:
            print(f"WARN: no download found for video {youtube_track.video_id}")
            self.ui.download_progress.setVisible(False)
            self.ui.download_error.setVisible(False)
            self.ui.cancel_button.setVisible(False)

    def _on_cancel_button_clicked(self):
        debug(f"_on_cancel_button_clicked({self.entry})")
        self.cancel_button_clicked.emit(self.entry)

    def _on_artist_clicked(self):
        debug(f"_on_artist_clicked({self.entry})")
        self.artist_clicked.emit(self.entry)

    def _on_album_clicked(self):
        debug(f"_on_album_clicked({self.entry})")
        self.album_clicked.emit(self.entry)

class DownloadsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()

    def entries(self) -> List:
        return [down["user_data"] for down in ytdownloader.downloads.values()]

    def entry_count(self) -> int:
        return len(ytdownloader.downloads)

class FinishedDownloadsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()

    def entries(self) -> List:
        return [down["user_data"] for down in ytdownloader.finished_downloads.values()]

    def entry_count(self) -> int:
        return len(ytdownloader.finished_downloads)

class DownloadsWidget(ListWidgetModelView):
    cancel_button_clicked = pyqtSignal(int)
    artist_clicked = pyqtSignal(int)
    album_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        w = DownloadsItemWidget(entry)
        w.cancel_button_clicked.connect(self._on_cancel_button_clicked)
        w.artist_clicked.connect(self._on_artist_clicked)
        w.album_clicked.connect(self._on_album_clicked)
        return w

    def _on_cancel_button_clicked(self, entry: str):
        row = self.model.index(entry)
        self.cancel_button_clicked.emit(row)

    def _on_artist_clicked(self, entry: str):
        row = self.model.index(entry)
        self.artist_clicked.emit(row)

    def _on_album_clicked(self, entry: str):
        row = self.model.index(entry)
        self.album_clicked.emit(row)