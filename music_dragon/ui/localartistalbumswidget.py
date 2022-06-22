from typing import List, Optional

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout

from music_dragon import localsongs
from music_dragon.localsongs import Mp3
from music_dragon.ui import resources
from music_dragon.repository import get_release_group, get_artist
from music_dragon.ui.listwidgetmodelview import ListWidgetModelView, ListWidgetModelViewItem, ListWidgetModel
from music_dragon.utils import make_pixmap_from_data


class LocalArtistAlbumsItemWidget(ListWidgetModelViewItem):
    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            # self.subtitle: Optional[QLabel] = None

    def __init__(self, album_group_leader: Mp3):
        super().__init__(entry=album_group_leader)

        self.album_group_leader = album_group_leader
        self.ui = LocalArtistAlbumsItemWidget.Ui()
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
        # self.ui.title.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        # subtitle
        # self.ui.subtitle = QLabel()
        # self.ui.subtitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # self.ui.subtitle.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # font = self.ui.subtitle.font()
        # font.setPointSize(10)
        # self.ui.subtitle.setFont(font)

        # build
        self.ui.layout = QHBoxLayout()
        self.ui.layout.setSpacing(12)
        self.ui.layout.addWidget(self.ui.cover)

        self.ui.inner_layout = QVBoxLayout()
        self.ui.inner_layout.setSpacing(0)
        self.ui.inner_layout.addWidget(self.ui.title)
        # self.ui.inner_layout.addWidget(self.ui.subtitle)
        self.ui.layout.addLayout(self.ui.inner_layout)

        self.setLayout(self.ui.layout)

    def invalidate(self):
        # cover
        self.ui.cover.setPixmap(make_pixmap_from_data(self.album_group_leader.image, default=resources.COVER_PLACEHOLDER_PIXMAP))

        # title
        self.ui.title.setText(self.album_group_leader.album)

        # subtitle
        # self.ui.subtitle.setText("")

class LocalArtistAlbumsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()
        self.artist: Optional[str] = None
        self.albums = []

    def set(self, mp3: Mp3):
        self.artist = mp3.artist
        albums = {}
        for mp3 in localsongs.mp3s:
            if mp3.artist == self.artist:
                if mp3.album not in albums or not albums[mp3.album].image:
                    albums[mp3.album] = mp3

        self.albums = list(albums.values())

    def entries(self) -> List:
        return self.albums

class LocalArtistAlbumsWidget(ListWidgetModelView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        return LocalArtistAlbumsItemWidget(entry)