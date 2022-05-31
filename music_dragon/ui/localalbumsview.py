from typing import Any, Optional

from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QModelIndex, QAbstractListModel, QVariant, pyqtSignal
from PyQt5.QtGui import QPainter, QMouseEvent
from PyQt5.QtWidgets import QStyledItemDelegate, QWidget, QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout, QSpacerItem, \
    QGridLayout, QListView

from music_dragon import localsongs
from music_dragon.log import debug
from music_dragon.ui import resources
from music_dragon.ui.clickablelabel import ClickableLabel
from music_dragon.utils import make_icon_from_data


class LocalAlbumsItemRole:
    TITLE = Qt.DisplayRole
    IMAGE = Qt.DecorationRole
    ARTIST = Qt.UserRole


class LocalAlbumsItemWidget(QWidget):
    artist_clicked = pyqtSignal(int)
    album_clicked = pyqtSignal(int)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.artist: Optional[QLabel] = None

    def __init__(self, parent, row, title, artist, image):
        super().__init__(parent)

        self.row = row
        self.title = title
        self.artist = artist
        self.image = image

        self.ui = LocalAlbumsItemWidget.Ui()
        self.setup()
        self.setAutoFillBackground(True)
        self.invalidate()


    def setup(self):
        # title
        self.ui.title = QLabel()
        self.ui.title.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        # artist
        self.ui.artist = ClickableLabel()
        self.ui.artist.set_underline_on_hover(True)
        f = self.ui.artist.font()
        f.setPointSize(10)
        self.ui.artist.setFont(f)
        self.ui.artist.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ui.artist.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.ui.artist.set_underline_on_hover(True)
        self.ui.artist.clicked.connect(self._on_artist_clicked)

        # build
        outer_layout = QHBoxLayout()
        outer_layout.setSpacing(4)
        # outer_layout.addWidget(self.ui.cover)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)

        subtitle_layout = QHBoxLayout()
        subtitle_layout.setSpacing(0)
        subtitle_layout.addWidget(self.ui.artist)
        subtitle_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        subtitle_layout.setContentsMargins(0, 0, 0, 0)

        content_layout.addWidget(self.ui.title)
        content_layout.addLayout(subtitle_layout)

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(8, 0, 0, 0)

        grid_layout.addLayout(content_layout, 0, 0)

        outer_layout.addLayout(grid_layout)

        self.setLayout(outer_layout)

    def invalidate(self):
        # title
        self.ui.title.setText(self.title)

        # artist
        self.ui.artist.setText(self.artist)

    def _on_artist_clicked(self):
        debug(f"_on_artist_clicked({self.artist})")
        self.artist_clicked.emit(self.row)

    def sizeHint(self) -> QSize:
        sz = super().sizeHint()
        return QSize(sz.width(), 48)


class LocalAlbumsItemDelegate(QStyledItemDelegate):
    artist_clicked = pyqtSignal(int)

    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        ICON_TO_TEXT_SPACING = 9

        painter.save()

        title: str = index.data(LocalAlbumsItemRole.TITLE)
        artist: str = index.data(LocalAlbumsItemRole.ARTIST)
        image: bytes = index.data(LocalAlbumsItemRole.IMAGE)

        main_rect = option.rect
        x = main_rect.x()
        y = main_rect.y()
        w = main_rect.width()
        h = main_rect.height()

        # Icon
        icon = make_icon_from_data(image, default=resources.COVER_PLACEHOLDER_ICON)
        icon_size = QSize(48, 48)
        icon_rect = QRect(x, y, icon_size.width(), icon_size.height())
        icon.paint(painter, icon_rect)
        # debug(f"Drawing icon of size {icon_size}")

        # Title
        if title:
            title_y = int(y + h / 2 - 5) if title and artist else int(y + h / 2 + 5)
            title_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING, title_y)
            painter.drawText(title_position, title)

        # Subtitle
        if artist:
            subtitle_y = int(y + h / 2 + 14)
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)

            artist_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING, subtitle_y)
            painter.drawText(artist_position, artist)

        painter.restore()

    def sizeHint(self, option: 'QStyleOptionViewItem', index: QModelIndex) -> QSize:
        sz = super(LocalAlbumsItemDelegate, self).sizeHint(option, index)
        return QSize(sz.width(), 48)

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> QWidget:
        title: str = index.data(LocalAlbumsItemRole.TITLE)
        artist: str = index.data(LocalAlbumsItemRole.ARTIST)
        image: bytes = index.data(LocalAlbumsItemRole.IMAGE)

        debug(f"Create editor for row with (title={title}, artist={artist})")
        editor = LocalAlbumsItemWidget(parent=parent, row=index.row(), title=title, artist=artist, image=image)

        editor.artist_clicked.connect(self._on_artist_clicked)
        editor.adjustSize()
        return editor

    def updateEditorGeometry(self, editor: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        # debug("updateEditorGeometry")
        rect = option.rect
        rect.setX(rect.x() + 48)
        rect.setY(rect.y())
        editor.setGeometry(rect)

    def _on_artist_clicked(self, row: int):
        debug(f"_on_artist_clicked at row {row}")
        self.artist_clicked.emit(row)


class LocalAlbumsModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.localalbums = []

    def reload(self):
        mp3s_by_albums = {}
        for mp3 in localsongs.mp3s:
            if mp3.album and (mp3.album not in mp3s_by_albums or not mp3s_by_albums[mp3.album].image):
                mp3s_by_albums[mp3.album] = mp3

        self.localalbums = list(mp3s_by_albums.values())

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsEditable | Qt.ItemIsSelectable

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.localalbums)

    def entry(self, row: int):
        return self.localalbums[row]

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()

        row = index.row()

        if row < 0 or row >= self.rowCount():
            return QVariant()

        mp3: localsongs.Mp3 = self.localalbums[row]

        if role == LocalAlbumsItemRole.TITLE:
            if mp3.album:
                return mp3.album
            return ""

        if role == LocalAlbumsItemRole.ARTIST:
            if mp3.artist:
                return mp3.artist
            return ""

        if role == LocalAlbumsItemRole.IMAGE:
            return mp3.image

        return QVariant()

    def update_row(self, row, roles=None):
        if row < 0 or row >= self.rowCount():
            return

        index = self.index(row)

        self.dataChanged.emit(index, index, roles or [])

class LocalAlbumsView(QListView):
    row_clicked = pyqtSignal(int)
    row_double_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit_index = None
        self.setMouseTracking(True)
        self.clicked.connect(self._on_item_clicked)
        self.doubleClicked.connect(self._on_item_double_clicked)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        # debug("mouseMoveEvent")
        index = self.indexAt(e.pos())
        if self.edit_index == index:
            return

        if self.edit_index and self.edit_index != index:
            self.closePersistentEditor(self.edit_index)

        self.edit_index = index
        self.openPersistentEditor(self.edit_index)

    def _on_item_clicked(self, idx: QModelIndex):
        self.row_clicked.emit(idx.row())

    def _on_item_double_clicked(self, idx: QModelIndex):
        self.row_double_clicked.emit(idx.row())