from typing import Optional, List

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QGridLayout


from music_dragon import ytdownloader, localsongs
from music_dragon.localsongs import Mp3
from music_dragon.ui import resources
from music_dragon.ui.listwidgetmodelview import ListWidgetModel, ListWidgetModelViewItem, ListWidgetModelView
from music_dragon.utils import make_pixmap_from_data


class LocalAlbumTracksItemWidget(ListWidgetModelViewItem):
    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None

    def __init__(self, mp3: Mp3):
        super().__init__(entry=mp3)

        self.mp3 = mp3
        self.ui = LocalAlbumTracksItemWidget.Ui()
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
        self.ui.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


        # build
        layout = QHBoxLayout()
        layout.setSpacing(4)
        layout.addWidget(self.ui.cover)

        inner_layout = QGridLayout()
        inner_layout.setContentsMargins(8, 0, 0, 0)
        inner_layout.addWidget(self.ui.title, 0, 0)
        layout.addLayout(inner_layout)

        self.setLayout(layout)

    def invalidate(self):
        # cover
        self.ui.cover.setPixmap(make_pixmap_from_data(self.mp3.image, default=resources.COVER_PLACEHOLDER_PIXMAP))

        # title
        self.ui.title.setText(self.mp3.title())

class LocalAlbumTracksModel(ListWidgetModel):
    def __init__(self):
        super().__init__()
        self.artist: Optional[str] = None
        self.album: Optional[str] = None
        self.mp3s = []

    def set(self, mp3: Mp3):
        self.artist = mp3.artist
        self.album = mp3.album
        self.mp3s = []
        for mp3 in localsongs.mp3s:
            if mp3.artist == self.artist and mp3.album == self.album:
                self.mp3s.append(mp3)

        self.mp3s = sorted(self.mp3s, key=lambda mp3: mp3.track_num or 9999)

    def entries(self) -> List:
        return self.mp3s

class LocalAlbumTracksWidget(ListWidgetModelView):
    download_button_clicked = pyqtSignal(int)
    open_video_button_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        w = LocalAlbumTracksItemWidget(entry)
        return w