from typing import List, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QGridLayout, QProgressBar

import ui
import ytdownloader
from repository import get_track, Track, get_youtube_track
from ui.listwidgetmodelview import ListWidgetModelView, ListWidgetModelViewItem, ListWidgetModel
from utils import make_pixmap_from_data


class DownloadsItemItemWidget(ListWidgetModelViewItem):
    download_button_clicked = pyqtSignal(str)
    open_video_button_clicked = pyqtSignal(str)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
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

        self.ui = DownloadsItemItemWidget.Ui()
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

        # download progress
        self.ui.download_progress = QProgressBar()
        self.ui.download_progress.setMaximumHeight(8)
        self.ui.download_progress.setTextVisible(False)
        self.ui.download_progress.setMinimum(0)
        self.ui.download_progress.setMaximum(100)
        self.ui.download_progress.setOrientation(Qt.Horizontal)
        self.ui.download_progress.setValue(0)
        self.ui.download_progress.setVisible(False)

        # build
        layout = QHBoxLayout()
        layout.setSpacing(4)
        layout.addWidget(self.ui.cover)

        inner_layout = QGridLayout()
        inner_layout.addWidget(self.ui.title, 0, 0)
        inner_layout.setContentsMargins(8, 0, 0, 0)
        inner_layout.addWidget(self.ui.download_progress, 0, 0, alignment=Qt.AlignBottom)
        layout.addLayout(inner_layout)

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

        # progress
        youtube_track = get_youtube_track(self.track.youtube_track_id)
        download = ytdownloader.get_download(youtube_track.video_id)

        if download:
            self.ui.download_progress.setVisible(download["status"] == "downloading")
            self.ui.download_progress.setValue(round(download["progress"]))
        else:
            print(f"WARN: no download found for video {youtube_track.video_id}")


class DownloadsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()

    def entries(self) -> List:
        return [down["user_data"] for down in ytdownloader.downloads.values()]

    def entry_count(self) -> int:
        return len(ytdownloader.downloads)

class DownloadsWidget(ListWidgetModelView):

    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        w = DownloadsItemItemWidget(entry)
        return w
