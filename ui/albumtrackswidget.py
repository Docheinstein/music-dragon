from typing import Optional, List

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QGridLayout, QPushButton, \
    QProgressBar

import ui
from repository import Track, get_release, get_track
from ui.listwidgetmodelview import ListWidgetModel, ListWidgetModelViewItem, ListWidgetModelView
from utils import make_pixmap_from_data


class AlbumTracksItemWidget(ListWidgetModelViewItem):
    # download_track_clicked = pyqtSignal(MbTrack)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.download_button: Optional[QPushButton] = None
            self.download_progress: Optional[QProgressBar] = None
            self.layout = None
            self.inner_layout = None

    def __init__(self, track_id: str):
        super().__init__(entry=track_id)

        self.track_id = track_id
        self.track: Track = get_track(self.track_id)
        if not self.track:
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
        self.ui.title = QLabel()
        self.ui.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # download button
        self.ui.download_button = QPushButton()
        self.ui.download_button.setVisible(False)
        self.ui.download_button.setIcon(ui.resources.DOWNLOAD_ICON)
        self.ui.download_button.setFlat(True)
        self.ui.download_button.setCursor(Qt.PointingHandCursor)
        self.ui.download_button.setIconSize(QSize(24, 24))
        # self.ui.download_button.clicked.connect(self._on_download_track_clicked)

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
        if self.track_id is None:
            return

        self.track = get_track(self.track_id)
        release_group = self.track.release().release_group()

        # cover
        cover = release_group.images.preferred_image()
        self.ui.cover.setPixmap(make_pixmap_from_data(cover, default=ui.resources.COVER_PLACEHOLDER_PIXMAP))

        # title
        self.ui.title.setText(self.track.title)

        # TODO: download/download progress

class AlbumTracksModel(ListWidgetModel):
    def __init__(self):
        super().__init__()
        self.release_id: Optional[str] = None

    def entries(self) -> List:
        release = get_release(self.release_id)
        return release.track_ids if release else []

    def entry_count(self) -> int:
        release = get_release(self.release_id)
        return release.track_count() if release else 0

class AlbumTracksWidget(ListWidgetModelView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        return AlbumTracksItemWidget(entry)

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
    #             track_widget.ui.cover.setPixmap(QPixmap(ui.resources.DEFAULT_COVER_PLACEHOLDER_IMAGE_PATH))
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