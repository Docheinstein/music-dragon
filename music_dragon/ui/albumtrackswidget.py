from typing import Optional, List

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QGridLayout, QPushButton, \
    QProgressBar


from music_dragon import ytdownloader
from music_dragon.ui import resources
from music_dragon.log import debug
from music_dragon.repository import Track, get_release, get_track, get_youtube_track
from music_dragon.ui.listwidgetmodelview import ListWidgetModel, ListWidgetModelViewItem, ListWidgetModelView
from music_dragon.utils import make_pixmap_from_data


class AlbumTracksItemWidget(ListWidgetModelViewItem):
    link_button_clicked = pyqtSignal(str)
    download_button_clicked = pyqtSignal(str)
    open_video_button_clicked = pyqtSignal(str)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.subtitle: Optional[QLabel] = None
            self.link_button: Optional[QPushButton] = None
            self.download_button: Optional[QPushButton] = None
            self.open_video_button: Optional[QPushButton] = None
            self.download_progress: Optional[QProgressBar] = None

    def __init__(self, track_id: str, show_youtube_titles=False):
        super().__init__(entry=track_id)

        self.show_youtube_title = show_youtube_titles
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
        self.ui.cover.setMaximumSize(QSize(48, 48))
        self.ui.cover.setScaledContents(True)

        # title
        self.ui.title = QLabel()
        self.ui.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # subtitle
        self.ui.subtitle = QLabel()
        self.ui.subtitle.setVisible(True)
        f = self.ui.subtitle.font()
        f.setItalic(True)
        f.setPointSize(f.pointSize() - 2)
        self.ui.subtitle.setFont(f)
        self.ui.subtitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # download button
        self.ui.link_button = QPushButton()
        # self.ui.link_button.setVisible(False)
        self.ui.link_button.setIcon(resources.LINK_ICON)
        self.ui.link_button.setFlat(True)
        self.ui.link_button.setCursor(Qt.PointingHandCursor)
        self.ui.link_button.setIconSize(QSize(24, 24))
        self.ui.link_button.setToolTip(f"Set YouTube URL")
        self.ui.link_button.clicked.connect(self._on_link_button_clicked)
        # szp = self.ui.link_button.sizePolicy()
        # szp.setRetainSizeWhenHidden(True)
        # self.ui.link_button.setSizePolicy(szp)

        # download button
        self.ui.download_button = QPushButton()
        self.ui.download_button.setVisible(False)
        self.ui.download_button.setIcon(resources.DOWNLOAD_ICON)
        self.ui.download_button.setFlat(True)
        self.ui.download_button.setCursor(Qt.PointingHandCursor)
        self.ui.download_button.setIconSize(QSize(24, 24))
        self.ui.download_button.setToolTip(f"Download song from YouTube")
        self.ui.download_button.clicked.connect(self._on_download_button_clicked)
        szp = self.ui.download_button.sizePolicy()
        szp.setRetainSizeWhenHidden(True)
        self.ui.download_button.setSizePolicy(szp)

        # open video
        self.ui.open_video_button = QPushButton()
        self.ui.open_video_button.setVisible(False)
        self.ui.open_video_button.setIcon(resources.OPEN_LINK_ICON)
        self.ui.open_video_button.setFlat(True)
        self.ui.open_video_button.setCursor(Qt.PointingHandCursor)
        self.ui.open_video_button.setIconSize(QSize(24, 24))
        self.ui.open_video_button.setToolTip(f"Open song in YouTube")
        self.ui.open_video_button.clicked.connect(self._on_open_video_button_clicked)

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
        inner_layout.setContentsMargins(8, 0, 0, 0)
        inner_layout.addWidget(self.ui.title, 0, 0)
        inner_layout.addWidget(self.ui.subtitle, 0, 0, alignment=Qt.AlignBottom)
        inner_layout.addWidget(self.ui.download_progress, 0, 0, alignment=Qt.AlignBottom)
        layout.addLayout(inner_layout)


        layout.addWidget(self.ui.link_button)
        layout.addWidget(self.ui.open_video_button)
        layout.addWidget(self.ui.download_button)

        self.setLayout(layout)

    def invalidate(self):
        if self.track_id is None:
            return

        self.track = get_track(self.track_id)
        release_group = self.track.release().release_group()

        locally_available = self.track.is_locally_available()

        # cover
        cover = release_group.preferred_front_cover()
        self.ui.cover.setPixmap(make_pixmap_from_data(cover, default=resources.COVER_PLACEHOLDER_PIXMAP))
        if locally_available:
            self.ui.cover.setStyleSheet(resources.LOCALLY_AVAILABLE_STYLESHEET)
        else:
            self.ui.cover.setStyleSheet(resources.LOCALLY_UNAVAILABLE_STYLESHEET)

        # title
        self.ui.title.setText(self.track.title)

        # download
        youtube_track = get_youtube_track(self.track.youtube_track_id)
        download = ytdownloader.get_download(youtube_track.video_id) if youtube_track else None

        if youtube_track:
            self.ui.subtitle.setText(youtube_track.video_title)
            self.ui.subtitle.setVisible(True)

            self.ui.open_video_button.setVisible(True)

            if download and download["user_data"]["type"] == "official":
                self.ui.download_progress.setVisible(download["status"] == "downloading")
                self.ui.download_progress.setValue(round(download["progress"]))

                self.ui.download_button.setVisible(False)
                # self.ui.open_video_button.setVisible(False)

            else:
                self.ui.download_progress.setVisible(False)

                if locally_available:
                    self.ui.download_button.setVisible(False)
                    # self.ui.open_video_button.setVisible(False)
                else:
                    self.ui.download_button.setVisible(True)

                    # self.ui.open_video_button.setVisible(True)
                    # self.ui.open_video_button.setToolTip(f"Open")
        else:
            self.ui.subtitle.setVisible(False)
            self.ui.download_progress.setVisible(False)
            self.ui.download_button.setVisible(False)
            self.ui.open_video_button.setVisible(False)

        if self.ui.download_progress.isVisible():
            self.ui.subtitle.setVisible(False)

        if not self.show_youtube_title:
            self.ui.subtitle.setVisible(False)

    def _on_link_button_clicked(self):
        debug(f"_on_link_button_clicked({self._on_link_button_clicked})")
        self.link_button_clicked.emit(self.track_id)

    def _on_download_button_clicked(self):
        debug(f"on_download_button_clicked({self.track_id})")
        self.download_button_clicked.emit(self.track_id)

    def _on_open_video_button_clicked(self):
        debug(f"on_open_video_button_clicked({self.track_id})")
        self.open_video_button_clicked.emit(self.track_id)

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
    link_button_clicked = pyqtSignal(int)
    download_button_clicked = pyqtSignal(int)
    open_video_button_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.show_youtube_titles = False

    def set_show_youtube_titles(self, show):
        if show == self.show_youtube_titles:
            return
        self.show_youtube_titles = show
        self.invalidate()

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        w = AlbumTracksItemWidget(entry, self.show_youtube_titles)
        w.link_button_clicked.connect(self._on_link_button_clicked)
        w.download_button_clicked.connect(self._on_download_button_clicked)
        w.open_video_button_clicked.connect(self._on_open_video_button_clicked)
        return w

    def _on_link_button_clicked(self, entry: str):
        row = self.model.index(entry)
        self.link_button_clicked.emit(row)

    def _on_download_button_clicked(self, entry: str):
        row = self.model.index(entry)
        self.download_button_clicked.emit(row)

    def _on_open_video_button_clicked(self, entry: str):
        row = self.model.index(entry)
        self.open_video_button_clicked.emit(row)