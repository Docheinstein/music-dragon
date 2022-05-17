from typing import List, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QListWidget, QWidget, QLabel, QSizePolicy, QHBoxLayout, QGridLayout, QPushButton, \
    QProgressBar, QListWidgetItem

import globals
from entities import YtTrack
from log import debug
from musicbrainz import MbReleaseGroup
from repository import get_release_group
from utils import make_pixmap_from_data


class ArtistAlbumsItemWidget(QWidget):
    # download_track_clicked = pyqtSignal(MbTrack)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            # self.download_button: Optional[QPushButton] = None
            # self.download_progress: Optional[QProgressBar] = None

    def __init__(self, release_group_id: str):
        super().__init__()

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

        # build
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(self.ui.cover)

        inner_layout = QGridLayout()
        inner_layout.addWidget(self.ui.title, 0, 0)
        layout.addLayout(inner_layout)

        self.setLayout(layout)

    def invalidate(self):
        self.release_group = get_release_group(self.release_group_id)

        # cover
        cover = self.release_group.images.preferred_image()
        self.ui.cover.setPixmap(make_pixmap_from_data(cover, default=globals.COVER_PLACEHOLDER_PIXMAP))

        # title
        self.ui.title.setText(self.release_group.title)


class ArtistAlbumsModel:
    def __init__(self):
        self.release_group_id: Optional[str] = None

class ArtistAlbumsWidget(QListWidget):
    row_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model: Optional[ArtistAlbumsModel] = None
        self.itemClicked.connect(self._on_item_clicked)

    def set_model(self, model: ArtistAlbumsModel) -> None:
        self.model = model
        self.invalidate()

    def invalidate(self):
        self.clear()
        debug(f"AlbumTracksWidget.invalidate()")
        release = repository.get_release(self.model.release_id)
        if not release:
            debug(f"AlbumTracksWidget.invalidate(): nothing to do for release {self.model.release_id}")
            return
        debug(f"AlbumTracksWidget.invalidate(): adding {release.track_count()} rows")
        for idx, track_id in enumerate(release.track_ids):
            self._add_row(track_id)

    def update_row(self, track_id: str):
        release = repository.get_release(self.model.release_id)
        if not release:
            print(f"WARN: track row for id {track_id} not found")
            return

        for idx, track_id_ in enumerate(release.track_ids):
            if track_id_ == track_id:
                self.update_row_at(idx)
                return

    def update_row_at(self, idx: int):
        item = self.item(idx)
        widget: ArtistAlbumsItemWidget = self.itemWidget(item)
        widget.invalidate()

    def _add_row(self, track_id):
        item = QListWidgetItem()
        widget = ArtistAlbumsItemWidget(track_id)
        item.setSizeHint(widget.sizeHint())

        self.addItem(item)
        self.setItemWidget(item, widget)

    def _on_item_clicked(self, item: QListWidgetItem):
        debug(f"on_item_clicked at row {self.row(item)}")
        self.row_clicked.emit(self.row(item))

    #
    # def set_youtube_track(self, mbtrack: MbTrack, yttrack: YtTrack):
    #     for idx, track in enumerate(self.tracks):
    #         if track.id == mbtrack.id:
    #             item = self.item(idx)
    #             track_widget: AlbumTracksItemWidget = self.itemWidget(item)
    #
    #             track.youtube_track = yttrack
    #             track_widget.ui.download_button.setVisible(True)
    #             track_widget.ui.download_button.setToolTip(f"Download {yttrack.video_title}  [{yttrack.video_id}]")
    #
    # def set_download_enabled(self, mbtrack: MbTrack, enabled):
    #     for idx, track in enumerate(self.tracks):
    #         if track.id == mbtrack.id:
    #             item = self.item(idx)
    #             track_widget: AlbumTracksItemWidget = self.itemWidget(item)
    #
    #             track_widget.ui.download_button.setVisible(enabled)
    #
    # def set_download_progress_visible(self, mbtrack: MbTrack, visibile):
    #     for idx, track in enumerate(self.tracks):
    #         if track.id == mbtrack.id:
    #             item = self.item(idx)
    #             track_widget: AlbumTracksItemWidget = self.itemWidget(item)
    #
    #             track_widget.ui.download_progress.setVisible(visibile)
    #
    # def set_download_progress(self, mbtrack: MbTrack, percentage: int):
    #     for idx, track in enumerate(self.tracks):
    #         if track.id == mbtrack.id:
    #             item = self.item(idx)
    #             track_widget: AlbumTracksItemWidget = self.itemWidget(item)
    #
    #             track_widget.ui.download_progress.setValue(percentage)
    #
    # def on_download_track_clicked(self, track: MbTrack):
    #     self.download_track_clicked.emit(track)
