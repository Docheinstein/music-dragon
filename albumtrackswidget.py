from typing import List, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QListWidget, QWidget, QLabel, QSizePolicy, QHBoxLayout, QGridLayout, QPushButton, \
    QProgressBar, QListWidgetItem

import globals
import repository
from entities import YtTrack
from log import debug
from musicbrainz import MbTrack, MbRelease
from utils import make_pixmap_from_data


class AlbumTracksItemWidget(QWidget):
    download_track_clicked = pyqtSignal(MbTrack)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.download_button: Optional[QPushButton] = None
            self.download_progress: Optional[QProgressBar] = None
            self.layout = None
            self.inner_layout = None

    def __init__(self, track_id: str):
        super().__init__()

        self.track_id = track_id
        self.track: MbTrack = repository.get_track(self.track_id)
        if not self.track_id:
            print(f"WARN: no track for id '{self.track_id}'")
            return

        self.ui = AlbumTracksItemWidget.Ui()
        self.setup()
        self.invalidate()


    def setup(self):
        # cover
        self.ui.cover = QLabel()
        self.ui.cover.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ui.cover.setMaximumSize(QSize(64, 64))
        self.ui.cover.setScaledContents(True)

        # title
        # self.ui.title = QLabel(track.title)
        self.ui.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # download button
        self.ui.download_button = QPushButton()
        self.ui.download_button.setVisible(False)
        self.ui.download_button.setIcon(globals.DOWNLOAD_ICON)
        self.ui.download_button.setFlat(True)
        self.ui.download_button.setCursor(Qt.PointingHandCursor)
        self.ui.download_button.setIconSize(QSize(24, 24))
        self.ui.download_button.clicked.connect(self._on_download_track_clicked)

        # download progress
        self.ui.download_progress = QProgressBar()
        self.ui.download_progress.setMaximumHeight(8)
        self.ui.download_progress.setTextVisible(False)
        self.ui.download_progress.setMinimum(0)
        self.ui.download_progress.setMaximum(100)
        self.ui.download_progress.setOrientation(Qt.Horizontal)
        self.ui.download_progress.setValue(20)
        self.ui.download_progress.setVisible(False)

        # build
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(self.ui.cover)

        inner_layout = QGridLayout()
        inner_layout.addWidget(self.ui.title, 0, 0)
        inner_layout.addWidget(self.ui.download_progress, 0, 0, alignment=Qt.AlignBottom)
        layout.addLayout(inner_layout)

        layout.addWidget(self.ui.download_button)

        self.setLayout(layout)

    def invalidate(self):
        release = repository.get_release(self.track.release_id)
        release_group = repository.get_release_group(release.release_group_id)

        # cover
        cover = release_group.images.preferred_image()
        if cover:
            self.ui.cover.setPixmap(make_pixmap_from_data(cover))
        else:
            self.ui.cover.setPixmap(QPixmap(globals.DEFAULT_COVER_PLACEHOLDER_IMAGE_PATH))

        # title
        self.ui.title.setText(release_group.title)

        # TODO: download/download progress

    def _on_download_track_clicked(self):
        pass
        # self.download_track_clicked.emit(self.track)

class AlbumTracksModel:
    def __init__(self):
        self.release_id: Optional[str] = None

class AlbumTracksWidget(QListWidget):
    row_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model: Optional[AlbumTracksModel] = None
        self.itemClicked.connect(self._on_item_clicked)

    def set_model(self, model: AlbumTracksModel) -> None:
        self.model = model
        self.invalidate()

    def invalidate(self):
        self.clear()
        debug(f"AlbumTracksWidget.invalidate()")
        release = repository.get_release(self.model.release_id)
        if not release:
            debug(f"AlbumTracksWidget.invalidate(): nothing to do")
            return
        debug(f"AlbumTracksWidget.invalidate(): adding {len(release.tracks)} rows")
        for idx, track in enumerate(release.tracks):
            self._add_row(track)

    def update_row(self, track_id: str):
        release = repository.get_release(self.model.release_id)
        if not release:
            print(f"WARN: track row for id {track_id} not found")
            return

        for idx, track in enumerate(release.tracks):
            if track.id == track_id:
                self.update_row_at(idx)
                return

    def update_row_at(self, idx: int):
        item = self.item(idx)
        widget: AlbumTracksItemWidget = self.itemWidget(item)
        widget.invalidate()

    def _add_row(self, result):
        item = QListWidgetItem()
        widget = AlbumTracksItemWidget(result)
        item.setSizeHint(widget.sizeHint())

        self.addItem(item)
        self.setItemWidget(item, widget)

    def _on_item_clicked(self, item: QListWidgetItem):
        debug(f"on_item_clicked at row {self.row(item)}")
        self.row_clicked.emit(self.row(item))
    #
    # def add_track(self, track: MbTrack):
    #     self.tracks.append(track)
    #
    #     item = QListWidgetItem()
    #     widget = AlbumTracksItemWidget(track)
    #     widget.download_track_clicked.connect(self.on_download_track_clicked)
    #     item.setSizeHint(widget.sizeHint())
    #
    #     self.addItem(item)
    #     self.setItemWidget(item, widget)
    #
    # def set_cover(self, cover):
    #     for idx, track in enumerate(self.tracks):
    #         item = self.item(idx)
    #         track_widget: AlbumTracksItemWidget = self.itemWidget(item)
    #         if cover:
    #             track_widget.ui.cover.setPixmap(make_pixmap_from_data(cover))
    #         else:
    #             track_widget.ui.cover.setPixmap(QPixmap(globals.DEFAULT_COVER_PLACEHOLDER_IMAGE_PATH))
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
    #
    # def on_item_clicked(self, item: QListWidgetItem):
    #     debug(f"on_item_clicked at row {self.row(item)}")
    #     self.row_clicked.emit(self.row(item))