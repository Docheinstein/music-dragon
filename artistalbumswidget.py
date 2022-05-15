from typing import List, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QListWidget, QWidget, QLabel, QSizePolicy, QHBoxLayout, QGridLayout, QPushButton, \
    QProgressBar, QListWidgetItem

import globals
from entities import MbTrack, YtTrack, MbReleaseGroup
from log import debug
from utils import make_pixmap_from_data


class ArtistAlbumsItemWidget(QWidget):
    # download_track_clicked = pyqtSignal(MbTrack)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            # self.download_button: Optional[QPushButton] = None
            # self.download_progress: Optional[QProgressBar] = None

    def __init__(self, album: MbReleaseGroup):
        super().__init__()
        self.album = album
        self.ui = ArtistAlbumsItemWidget.Ui()

        # cover
        self.ui.cover = QLabel()
        self.ui.cover.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ui.cover.setMaximumSize(QSize(64, 64))
        self.ui.cover.setScaledContents(True)
        cover = album.cover()
        if cover:
            self.ui.cover.setPixmap(make_pixmap_from_data(cover))
        else:
            self.ui.cover.setPixmap(QPixmap(globals.DEFAULT_COVER_PLACEHOLDER_IMAGE_PATH))

        # title
        # self.ui.title = QLabel(album.title)
        self.ui.title = QLabel(f"{album.title} [{album.year}]")
        self.ui.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        #
        # # download button
        # self.ui.download_button = QPushButton()
        # self.ui.download_button.setVisible(False)
        # self.ui.download_button.setIcon(globals.DOWNLOAD_ICON)
        # self.ui.download_button.setFlat(True)
        # self.ui.download_button.setCursor(Qt.PointingHandCursor)
        # self.ui.download_button.setIconSize(QSize(24, 24))
        # self.ui.download_button.clicked.connect(self.on_download_clicked)
        #
        # # download progress
        # self.ui.download_progress = QProgressBar()
        # self.ui.download_progress.setMaximumHeight(8)
        # self.ui.download_progress.setTextVisible(False)
        # self.ui.download_progress.setMinimum(0)
        # self.ui.download_progress.setMaximum(100)
        # self.ui.download_progress.setOrientation(Qt.Horizontal)
        # self.ui.download_progress.setValue(20)
        # self.ui.download_progress.setVisible(False)

        # build

        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(self.ui.cover)

        inner_layout = QGridLayout()
        inner_layout.addWidget(self.ui.title, 0, 0)
        # inner_layout.addWidget(self.ui.download_progress, 0, 0, alignment=Qt.AlignBottom)
        layout.addLayout(inner_layout)

        # layout.addWidget(self.ui.download_button)

        self.setLayout(layout)

    # def on_download_clicked(self):
    #     self.download_track_clicked.emit(self.track)



class ArtistAlbumsWidget(QListWidget):
    album_clicked = pyqtSignal(MbReleaseGroup)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.albums: List[MbReleaseGroup] = []
        self.itemDoubleClicked.connect(self.on_double_click)

    def clear(self) -> None:
        self.albums.clear()
        super().clear()

    def add_album(self, album: MbReleaseGroup):
        self.albums.append(album)

        item = QListWidgetItem()
        widget = ArtistAlbumsItemWidget(album)
        # widget.download_track_clicked.connect(self.on_download_track_clicked)
        item.setSizeHint(widget.sizeHint())

        self.addItem(item)
        self.setItemWidget(item, widget)

    def set_cover(self, release_group: MbReleaseGroup, cover):
        for idx, album in enumerate(self.albums):
            item = self.item(idx)
            album_widget: ArtistAlbumsItemWidget = self.itemWidget(item)
            if album.id == release_group.id:
                if cover:
                    album_widget.ui.cover.setPixmap(make_pixmap_from_data(cover))
                else:
                    album_widget.ui.cover.setPixmap(QPixmap(globals.DEFAULT_COVER_PLACEHOLDER_IMAGE_PATH))

    def on_double_click(self, item: QListWidgetItem):
        index = self.row(item)
        self.album_clicked.emit(self.albums[index])

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
