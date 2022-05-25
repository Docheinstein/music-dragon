from typing import List, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QGridLayout, QProgressBar, QPushButton, QVBoxLayout, \
    QSpacerItem

import localsongs
import ui
import ytdownloader
from log import debug
from repository import get_track, Track, get_youtube_track
from ui.clickablelabel import ClickableLabel
from ui.listwidgetmodelview import ListWidgetModelView, ListWidgetModelViewItem, ListWidgetModel
from utils import make_pixmap_from_data
from localsongs import Mp3

class LocalSongsItemWidget(ListWidgetModelViewItem):
    artist_clicked = pyqtSignal(Mp3)
    album_clicked = pyqtSignal(Mp3)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.artist: Optional[QLabel] = None
            self.album: Optional[QLabel] = None

    def __init__(self, mp3):
        super().__init__(entry=mp3)
        self.mp3 = mp3
        # self.track: Track = get_track(self.track_id)
        # if not self.track:
        #     print(f"WARN: no track for id '{self.track_id}'")
        #     return

        self.ui = LocalSongsItemWidget.Ui()
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
        self.ui.artist.set_underline_on_hover(True)
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

        outer_layout.addLayout(grid_layout)

        self.setLayout(outer_layout)

    def invalidate(self):
        # if self.entry is None:
        #     return
        #
        # mp3 = localsongs.get_mp3(*self.entry)
        #
        # if not mp3:
        #     return

        # image
        self.ui.cover.setPixmap(make_pixmap_from_data(self.mp3.image, default=ui.resources.COVER_PLACEHOLDER_PIXMAP))

        # title
        self.ui.title.setText(self.mp3.song)

        # artist
        self.ui.artist.setText(self.mp3.artist)

        # album
        self.ui.album.setText(self.mp3.album)

    def _on_artist_clicked(self):
        debug(f"_on_artist_clicked({self.entry})")
        self.artist_clicked.emit(self.entry)

    def _on_album_clicked(self):
        debug(f"_on_album_clicked({self.entry})")
        self.album_clicked.emit(self.entry)

class LocalSongsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()

    def entries(self) -> List:
        return localsongs.mp3s

    def entry_count(self) -> int:
        return len(localsongs.mp3s)

class LocalSongsWidget(ListWidgetModelView):
    artist_clicked = pyqtSignal(int)
    album_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        w = LocalSongsItemWidget(entry)
        w.artist_clicked.connect(self._on_artist_clicked)
        w.album_clicked.connect(self._on_album_clicked)
        return w

    def _on_artist_clicked(self, entry: str):
        row = self.model.index(entry)
        self.artist_clicked.emit(row)

    def _on_album_clicked(self, entry: str):
        row = self.model.index(entry)
        self.album_clicked.emit(row)