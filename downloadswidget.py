from typing import List, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QListWidget, QWidget, QLabel, QSizePolicy, QHBoxLayout, QGridLayout, QPushButton, \
    QProgressBar, QListWidgetItem

import globals
from entities import YtTrack
from log import debug
from musicbrainz import MbTrack
from utils import make_pixmap_from_data


class DownloadsItemWidget(QWidget):
    download_track_clicked = pyqtSignal(MbTrack)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.download_progress: Optional[QProgressBar] = None

    def __init__(self, track: YtTrack):
        super().__init__()
        self.track = track
        self.ui = DownloadsItemWidget.Ui()

        # cover
        self.ui.cover = QLabel()
        self.ui.cover.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ui.cover.setMaximumSize(QSize(64, 64))
        self.ui.cover.setScaledContents(True)
        cover = track.mb_track.release.release_group.cover()
        if cover:
            self.ui.cover.setPixmap(make_pixmap_from_data(cover))
        else:
            self.ui.cover.setPixmap(QPixmap(globals.DEFAULT_COVER_PLACEHOLDER_IMAGE_PATH))

        # title
        self.ui.title = QLabel(track.mb_track.title)
        self.ui.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # # download progress
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

        self.setLayout(layout)


class DownloadsWidget(QListWidget):
    download_track_clicked = pyqtSignal(MbTrack)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracks: List[YtTrack] = []

    def clear(self) -> None:
        self.tracks.clear()
        super().clear()

    def add_track(self, track: YtTrack):
        self.tracks.append(track)

        item = QListWidgetItem()
        widget = DownloadsItemWidget(track)
        item.setSizeHint(widget.sizeHint())

        self.addItem(item)
        self.setItemWidget(item, widget)

    def remove_track(self, track: YtTrack):
        for i in range(len(self.tracks)):
            if self.tracks[i].video_id == track.video_id:
                self.takeItem(i)
                self.tracks.remove(track)
                return
        print(f"WARN: cannot find track {track.mb_track.title} among downloads")
    #
    # def set_cover(self, cover):
    #     for idx, track in enumerate(self.tracks):
    #         item = self.item(idx)
    #         track_widget: DownloadsItemWidget = self.itemWidget(item)
    #         if cover:
    #             track_widget.ui.cover.setPixmap(make_pixmap_from_data(cover))
    #         else:
    #             track_widget.ui.cover.setPixmap(QPixmap(globals.DEFAULT_COVER_PLACEHOLDER_IMAGE_PATH))
    #


    def set_download_progress_visible(self, yttrack: YtTrack, visibile):
        for idx, track in enumerate(self.tracks):
            if track.video_id == yttrack.video_id:
                item = self.item(idx)
                track_widget: DownloadsItemWidget = self.itemWidget(item)

                track_widget.ui.download_progress.setVisible(visibile)

    def set_download_progress(self, yttrack: YtTrack, percentage: int):
        for idx, track in enumerate(self.tracks):
            if track.video_id == yttrack.video_id:
                item = self.item(idx)
                track_widget: DownloadsItemWidget = self.itemWidget(item)

                track_widget.ui.download_progress.setValue(percentage)
    #
