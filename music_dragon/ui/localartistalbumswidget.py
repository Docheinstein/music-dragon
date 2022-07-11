from typing import List, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout, QPushButton

from music_dragon import localsongs, favourites
from music_dragon.localsongs import Mp3
from music_dragon.log import debug
from music_dragon.ui import resources
from music_dragon.ui.listwidgetmodelview import ListWidgetModelView, ListWidgetModelViewItem, ListWidgetModel
from music_dragon.utils import make_pixmap_from_data


class LocalArtistAlbumsItemWidget(ListWidgetModelViewItem):
    favourite_button_clicked = pyqtSignal(Mp3)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.subtitle: Optional[QLabel] = None
            self.fav: Optional[QPushButton] = None

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
        self.ui.title.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        # subtitle
        self.ui.subtitle = QLabel()
        self.ui.subtitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.ui.subtitle.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        font = self.ui.subtitle.font()
        font.setPointSize(10)
        self.ui.subtitle.setFont(font)

        # fav
        self.ui.fav = QPushButton()
        self.ui.fav.setIcon(resources.UNFAVOURITE_ICON)
        self.ui.fav.setIconSize(QSize(24, 24))
        self.ui.fav.setFlat(True)
        self.ui.fav.clicked.connect(self._on_fav_clicked)

        # build
        self.ui.layout = QHBoxLayout()
        self.ui.layout.setSpacing(12)
        self.ui.layout.addWidget(self.ui.cover)

        self.ui.inner_layout = QVBoxLayout()
        self.ui.inner_layout.setSpacing(0)
        self.ui.inner_layout.addWidget(self.ui.title)
        self.ui.inner_layout.addWidget(self.ui.subtitle)
        self.ui.layout.addLayout(self.ui.inner_layout)
        self.ui.layout.addWidget(self.ui.fav)

        self.setLayout(self.ui.layout)

    def invalidate(self):
        # cover
        self.ui.cover.setPixmap(make_pixmap_from_data(self.album_group_leader.image, default=resources.COVER_PLACEHOLDER_PIXMAP))

        # title
        self.ui.title.setText(self.album_group_leader.album)

        # subtitle
        self.ui.subtitle.setText(str(self.album_group_leader.year) if self.album_group_leader.year else "")

        # fav
        self.ui.fav.setIcon(resources.FAVOURITE_ICON
                            if favourites.is_favourite(artist=self.album_group_leader.artist, album=self.album_group_leader.album)
                            else resources.UNFAVOURITE_ICON)

    def _on_fav_clicked(self):
        debug(f"_on_fav_clicked({self.album_group_leader.album})")
        self.favourite_button_clicked.emit(self.album_group_leader)

class LocalArtistAlbumsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()
        self.artist: Optional[str] = None
        self.albums = []

    def set(self, mp3: Mp3):
        def is_better(m1: Mp3, m2: Mp3):
            if m1.year and not m2.year:
                return True
            if m1.image and not m2.image:
                return True
            return False
        self.artist = mp3.artist
        albums = {}
        for mp3 in localsongs.mp3s:
            if mp3.artist == self.artist:
                if mp3.album not in albums or is_better(mp3, albums[mp3.album]):
                    albums[mp3.album] = mp3

        debug([mp3.title() for mp3 in albums.values()])
        self.albums = sorted(list(albums.values()), key=lambda a: a.year or 9999)

    def entries(self) -> List:
        return self.albums

class LocalArtistAlbumsWidget(ListWidgetModelView):
    favourite_button_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        w = LocalArtistAlbumsItemWidget(entry)
        w.favourite_button_clicked.connect(self._on_favourite_button_clicked)
        return w

    def _on_favourite_button_clicked(self, entry: Mp3):
        row = self.model.index(entry)
        self.favourite_button_clicked.emit(row)