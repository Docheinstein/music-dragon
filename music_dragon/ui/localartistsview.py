from typing import Any

from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QModelIndex, QAbstractListModel, QVariant, pyqtSignal
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QStyledItemDelegate, QListView

from music_dragon import localsongs
from music_dragon.localsongs import Mp3
from music_dragon.ui import resources
from music_dragon.utils import make_icon_from_data


class LocalArtistsItemRole:
    NAME = Qt.DisplayRole
    IMAGE = Qt.DecorationRole

#
# class LocalArtistsItemWidget(QWidget):
#     artist_clicked = pyqtSignal(int)
#     album_clicked = pyqtSignal(int)
#
#     class Ui:
#         def __init__(self):
#             self.cover: Optional[QLabel] = None
#             self.title: Optional[QLabel] = None
#             self.artist: Optional[QLabel] = None
#             self.album: Optional[QLabel] = None
#
#     def __init__(self, parent, row, name, image):
#         super().__init__(parent)
#
#         self.row = row
#         self.name = name
#         self.image = image
#
#         self.ui = LocalArtistsItemWidget.Ui()
#         self.setup()
#         self.setAutoFillBackground(True)
#         self.invalidate()
#
#
#     def setup(self):
#         # title
#         self.ui.title = QLabel()
#         self.ui.title.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
#
#         # artist
#         self.ui.artist = ClickableLabel()
#         self.ui.artist.set_underline_on_hover(True)
#         f = self.ui.artist.font()
#         f.setPointSize(10)
#         self.ui.artist.setFont(f)
#         self.ui.artist.setAlignment(Qt.AlignLeft | Qt.AlignTop)
#         self.ui.artist.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
#         self.ui.artist.set_underline_on_hover(True)
#         self.ui.artist.clicked.connect(self._on_artist_clicked)
#
#         # -
#         dash = QLabel(" - ")
#         f = dash.font()
#         f.setPointSize(10)
#         dash.setFont(f)
#         dash.setAlignment(Qt.AlignLeft | Qt.AlignTop)
#         dash.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
#
#         # album
#         self.ui.album = ClickableLabel()
#         self.ui.album.set_underline_on_hover(True)
#         f = self.ui.album.font()
#         f.setPointSize(10)
#         self.ui.album.setFont(f)
#         self.ui.album.setAlignment(Qt.AlignLeft | Qt.AlignTop)
#         self.ui.album.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
#         self.ui.album.clicked.connect(self._on_album_clicked)
#
#         # build
#         outer_layout = QHBoxLayout()
#         outer_layout.setSpacing(4)
#         # outer_layout.addWidget(self.ui.cover)
#         outer_layout.setContentsMargins(0, 0, 0, 0)
#
#         content_layout = QVBoxLayout()
#         content_layout.setSpacing(0)
#
#         subtitle_layout = QHBoxLayout()
#         subtitle_layout.setSpacing(0)
#         subtitle_layout.addWidget(self.ui.artist)
#         subtitle_layout.addWidget(dash)
#         subtitle_layout.addWidget(self.ui.album)
#         subtitle_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
#         subtitle_layout.setContentsMargins(0, 0, 0, 0)
#
#         content_layout.addWidget(self.ui.title)
#         content_layout.addLayout(subtitle_layout)
#
#         grid_layout = QGridLayout()
#         grid_layout.setContentsMargins(8, 0, 0, 0)
#
#         grid_layout.addLayout(content_layout, 0, 0)
#
#         outer_layout.addLayout(grid_layout)
#
#         self.setLayout(outer_layout)
#
#     def invalidate(self):
#         # title
#         self.ui.title.setText(self.song)
#
#         # artist
#         self.ui.artist.setText(self.artist)
#
#         # album
#         self.ui.album.setText(self.album)
#
#     def _on_artist_clicked(self):
#         debug(f"_on_artist_clicked({self.artist})")
#         self.artist_clicked.emit(self.row)
#
#     def _on_album_clicked(self):
#         debug(f"_on_album_clicked({self.album})")
#         self.album_clicked.emit(self.row)
#
#     def sizeHint(self) -> QSize:
#         sz = super().sizeHint()
#         return QSize(sz.width(), 48)


class LocalArtistsItemDelegate(QStyledItemDelegate):
    # clicked = pyqtSignal(int)
    # album_clicked = pyqtSignal(int)

    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        ICON_TO_TEXT_SPACING = 9

        painter.save()

        name: str = index.data(LocalArtistsItemRole.NAME)
        image: bytes = index.data(LocalArtistsItemRole.IMAGE)

        main_rect = option.rect
        x = main_rect.x()
        y = main_rect.y()
        w = main_rect.width()
        h = main_rect.height()

        # # Icon
        icon = make_icon_from_data(image, default=resources.PERSON_PLACEHOLDER_ICON)
        icon_size = QSize(48, 48)
        icon_rect = QRect(x, y, icon_size.width(), icon_size.height())
        icon.paint(painter, icon_rect)
        # debug(f"Drawing icon of size {icon_size}")

        # Title
        if name:
            title_y = int(y + h / 2 + 5)
            title_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING, title_y)
            painter.drawText(title_position, name)

        painter.restore()

    def sizeHint(self, option: 'QStyleOptionViewItem', index: QModelIndex) -> QSize:
        sz = super(LocalArtistsItemDelegate, self).sizeHint(option, index)
        return QSize(sz.width(), 48)
    #
    # def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> QWidget:
    #     song: str = index.data(LocalArtistsItemRole.SONG)
    #     artist: str = index.data(LocalArtistsItemRole.ARTIST)
    #     album: str = index.data(LocalArtistsItemRole.ALBUM)
    #     image: bytes = index.data(LocalArtistsItemRole.IMAGE)
    #
    #     debug(f"Create editor for row with (song={song}, artist={artist}, album={album})")
    #     editor = LocalArtistsItemWidget(parent=parent, row=index.row(), artist=artist, album=album, song=song, image=image)
    #
    #     editor.artist_clicked.connect(self._on_artist_clicked)
    #     editor.album_clicked.connect(self._on_album_clicked)
    #     editor.adjustSize()
    #     return editor

    # def updateEditorGeometry(self, editor: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
    #     # debug("updateEditorGeometry")
    #     rect = option.rect
    #     rect.setX(rect.x() + 48)
    #     rect.setY(rect.y())
    #     editor.setGeometry(rect)

    # def _on_artist_clicked(self, row: int):
    #     debug(f"_on_artist_clicked at row {row}")
    #     self.artist_clicked.emit(row)
    #
    # def _on_album_clicked(self, row: int):
    #     debug(f"_on_album_clicked at row {row}")
    #     self.album_clicked.emit(row)


class LocalArtistsModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.localartists = []

    def reload(self):
        def is_better(m1: Mp3, m2: Mp3):
            if m1.year and not m2.year:
                return True
            if m1.image and not m2.image:
                return True
            if m1.year and m2.year and m1.year < m2.year:
                return True
            return False

        mp3s_by_artists = {}
        for mp3 in localsongs.mp3s:
            if mp3.artist and (mp3.artist not in mp3s_by_artists or is_better(mp3, mp3s_by_artists[mp3.artist])):
                mp3s_by_artists[mp3.artist] = mp3

        self.localartists = list(mp3s_by_artists.values())
        self.localartists = sorted(self.localartists, key=lambda mp3: mp3.artist.lower())

    # def flags(self, index: QModelIndex) -> Qt.ItemFlags:
    #     return super().flags(index) | Qt.ItemIsEditable | Qt.ItemIsSelectable

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.localartists)

    def entry(self, row: int):
        return self.localartists[row]

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()

        row = index.row()

        if row < 0 or row >= self.rowCount():
            return QVariant()

        mp3_group: localsongs.Mp3 = self.localartists[row]
        artist_name = mp3_group.artist

        if role == LocalArtistsItemRole.NAME:
            return artist_name

        if role == LocalArtistsItemRole.IMAGE:
            return mp3_group.image

        return QVariant()

    def update_row(self, row, roles=None):
        if row < 0 or row >= self.rowCount():
            return

        index = self.index(row)

        self.dataChanged.emit(index, index, roles or [])

class LocalArtistsView(QListView):
    row_clicked = pyqtSignal(int)
    # row_double_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit_index = None
        self.setMouseTracking(True)
        self.clicked.connect(self._on_item_clicked)
        # self.doubleClicked.connect(self._on_item_double_clicked)

    # def mouseMoveEvent(self, e: QMouseEvent) -> None:
    #     # debug("mouseMoveEvent")
    #     index = self.indexAt(e.pos())
    #     if self.edit_index == index:
    #         return
    #
    #     if self.edit_index and self.edit_index != index:
    #         self.closePersistentEditor(self.edit_index)
    #
    #     self.edit_index = index
    #     self.openPersistentEditor(self.edit_index)

    def _on_item_clicked(self, idx: QModelIndex):
        self.row_clicked.emit(idx.row())

    # def _on_item_double_clicked(self, idx: QModelIndex):
    #     self.row_double_clicked.emit(idx.row())