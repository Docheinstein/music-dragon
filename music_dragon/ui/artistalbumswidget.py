from typing import List, Optional

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout

from music_dragon.ui import resources
from music_dragon.repository import get_release_group, get_artist
from music_dragon.ui.listwidgetmodelview import ListWidgetModelView, ListWidgetModelViewItem, ListWidgetModel
from music_dragon.utils import make_pixmap_from_data


class ArtistAlbumsItemWidget(ListWidgetModelViewItem):
    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.subtitle: Optional[QLabel] = None

    def __init__(self, release_group_id: str):
        super().__init__(entry=release_group_id)

        self.release_group_id = release_group_id
        self.release_group = get_release_group(self.release_group_id)
        if not self.release_group:
            print(f"WARN: no release_group for id '{self.release_group_id}'")
            return

        self.ui = ArtistAlbumsItemWidget.Ui()
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

        # build
        self.ui.layout = QHBoxLayout()
        self.ui.layout.setSpacing(12)
        self.ui.layout.addWidget(self.ui.cover)

        self.ui.inner_layout = QVBoxLayout()
        self.ui.inner_layout.setSpacing(0)
        self.ui.inner_layout.addWidget(self.ui.title)
        self.ui.inner_layout.addWidget(self.ui.subtitle)
        self.ui.layout.addLayout(self.ui.inner_layout)

        self.setLayout(self.ui.layout)

    def invalidate(self):
        if self.release_group_id is None:
            return

        self.release_group = get_release_group(self.release_group_id)

        main = self.release_group.main_release()
        locally_available_track_count = main.locally_available_track_count() if main else 0
        if locally_available_track_count == 0:
            self.ui.cover.setStyleSheet(resources.LOCALLY_UNAVAILABLE_STYLESHEET)
        elif locally_available_track_count == main.track_count():
            self.ui.cover.setStyleSheet(resources.LOCALLY_AVAILABLE_STYLESHEET)
        else:
            self.ui.cover.setStyleSheet(resources.LOCALLY_PARTIALLY_AVAILABLE_STYLESHEET)

        # cover
        cover = self.release_group.preferred_front_cover()
        self.ui.cover.setPixmap(make_pixmap_from_data(cover, default=resources.COVER_PLACEHOLDER_PIXMAP))

        # title
        self.ui.title.setText(self.release_group.title)

        # subtitle
        self.ui.subtitle.setText(self.release_group.year())


class ArtistAlbumsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()
        self.artist_id: Optional[str] = None

    def entries(self) -> List:
        artist = get_artist(self.artist_id)
        return artist.release_group_ids if artist else []

    def entry_count(self) -> int:
        artist = get_artist(self.artist_id)
        return artist.release_group_count() if artist else 0

class ArtistAlbumsWidget(ListWidgetModelView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        return ArtistAlbumsItemWidget(entry)