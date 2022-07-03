from typing import Any, Optional

from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QModelIndex, QAbstractListModel, QVariant, pyqtSignal, \
    QSortFilterProxyModel
from PyQt5.QtGui import QPainter, QMouseEvent
from PyQt5.QtWidgets import QStyledItemDelegate, QWidget, QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout, QSpacerItem, \
    QGridLayout, QListView

from music_dragon import localsongs
from music_dragon.log import debug
from music_dragon.ui import resources
from music_dragon.ui.clickablelabel import ClickableLabel
from music_dragon.ui.listproxyview import ListProxyView
from music_dragon.utils import make_icon_from_data


class LocalSongsItemRole:
    SONG = Qt.DisplayRole
    IMAGE = Qt.DecorationRole
    ARTIST = Qt.UserRole
    ALBUM = Qt.UserRole + 1


class LocalSongsItemWidget(QWidget):
    artist_clicked = pyqtSignal(QModelIndex)
    album_clicked = pyqtSignal(QModelIndex)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.dash: Optional[QLabel] = None
            self.artist: Optional[QLabel] = None
            self.album: Optional[QLabel] = None
            self.subtitle_widget: Optional[QWidget] = None

    def __init__(self, parent, index, artist, album, song, image):
        super().__init__(parent)

        self.index = index
        self.artist = artist
        self.album = album
        self.song = song
        self.image = image

        self.ui = LocalSongsItemWidget.Ui()
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

        # -
        self.ui.dash = QLabel(" - ")
        f = self.ui.dash.font()
        f.setPointSize(10)
        self.ui.dash.setFont(f)
        self.ui.dash.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ui.dash.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # album
        self.ui.album = ClickableLabel()
        self.ui.album.set_underline_on_hover(True)
        f = self.ui.album.font()
        f.setPointSize(10)
        self.ui.album.setFont(f)
        self.ui.album.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ui.album.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.ui.album.clicked.connect(self._on_album_clicked)

        # build
        outer_layout = QHBoxLayout()
        outer_layout.setSpacing(4)
        # outer_layout.addWidget(self.ui.cover)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)

        self.ui.subtitle_widget = QWidget()
        subtitle_layout = QHBoxLayout()
        subtitle_layout.setSpacing(0)
        subtitle_layout.addWidget(self.ui.artist)
        subtitle_layout.addWidget(self.ui.dash)
        subtitle_layout.addWidget(self.ui.album)
        subtitle_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        subtitle_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.subtitle_widget.setLayout(subtitle_layout)

        content_layout.addWidget(self.ui.title)
        content_layout.addWidget(self.ui.subtitle_widget)

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(8, 0, 0, 0)

        grid_layout.addLayout(content_layout, 0, 0)

        outer_layout.addLayout(grid_layout)

        self.setLayout(outer_layout)

    def invalidate(self):
        # title
        self.ui.title.setText(self.song)

        # artist
        if self.artist:
            self.ui.artist.setVisible(True)
            self.ui.artist.setText(self.artist)
        else:
            self.ui.artist.setVisible(False)

        # album
        if self.album:
            self.ui.album.setVisible(True)
            self.ui.album.setText(self.album)
        else:
            self.ui.album.setVisible(False)

        if self.artist or self.album:
            self.ui.subtitle_widget.setVisible(True)
            self.ui.title.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
            if self.artist and self.album:
                self.ui.dash.setVisible(True)
        else:
            self.ui.subtitle_widget.setVisible(False)
            self.ui.dash.setVisible(False)
            self.ui.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    def _on_artist_clicked(self):
        debug(f"_on_artist_clicked({self.artist})")
        self.artist_clicked.emit(self.index)

    def _on_album_clicked(self):
        debug(f"_on_album_clicked({self.album})")
        self.album_clicked.emit(self.index)

    def sizeHint(self) -> QSize:
        sz = super().sizeHint()
        return QSize(sz.width(), 48)


class LocalSongsItemDelegate(QStyledItemDelegate):
    artist_clicked = pyqtSignal(int)
    album_clicked = pyqtSignal(int)

    def __init__(self, proxy: Optional[QSortFilterProxyModel] = None):
        super().__init__()
        self.proxy = proxy

    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        ICON_TO_TEXT_SPACING = 9

        painter.save()

        song: str = index.data(LocalSongsItemRole.SONG)
        artist: str = index.data(LocalSongsItemRole.ARTIST)
        album: str = index.data(LocalSongsItemRole.ALBUM)
        image: bytes = index.data(LocalSongsItemRole.IMAGE)

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
        if song:
            title_y = int(y + h / 2 - 5) if song and (artist or album) else int(y + h / 2 + 6)
            title_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING, title_y)
            painter.drawText(title_position, song)

        # Subtitle
        if artist or album:
            subtitle_y = int(y + h / 2 + 14)
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)


            def predict_width(text):
                return painter.boundingRect(QRect(0, 0, 0, 0), 0, text).width()

            artist_width = predict_width(artist)
            dash_width = predict_width(" - ")
            # album_width = predict_width(album)

            artist_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING, subtitle_y)
            painter.drawText(artist_position, artist)

            dash_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING + artist_width, subtitle_y)
            painter.drawText(dash_position, " - ")

            album_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING + artist_width + dash_width, subtitle_y)
            painter.drawText(album_position, album)

        painter.restore()

    def sizeHint(self, option: 'QStyleOptionViewItem', index: QModelIndex) -> QSize:
        sz = super(LocalSongsItemDelegate, self).sizeHint(option, index)
        return QSize(sz.width(), 48)

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> QWidget:
        song: str = index.data(LocalSongsItemRole.SONG)
        artist: str = index.data(LocalSongsItemRole.ARTIST)
        album: str = index.data(LocalSongsItemRole.ALBUM)
        image: bytes = index.data(LocalSongsItemRole.IMAGE)

        debug(f"Create editor for row with (song={song}, artist={artist}, album={album})")
        editor = LocalSongsItemWidget(parent=parent, index=index, artist=artist, album=album, song=song, image=image)

        editor.artist_clicked.connect(self._on_artist_clicked)
        editor.album_clicked.connect(self._on_album_clicked)
        editor.adjustSize()
        return editor

    def updateEditorGeometry(self, editor: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        # debug("updateEditorGeometry")
        rect = option.rect
        rect.setX(rect.x() + 48)
        rect.setY(rect.y())
        editor.setGeometry(rect)

    def _on_artist_clicked(self, index: QModelIndex):
        index = self.proxy.mapToSource(index) if self.proxy else index
        row = index.row()
        debug(f"_on_artist_clicked at row {row}")
        self.artist_clicked.emit(row)

    def _on_album_clicked(self, index: QModelIndex):
        index = self.proxy.mapToSource(index) if self.proxy else index
        row = index.row()
        debug(f"_on_album_clicked at row {row}")
        self.album_clicked.emit(row)


class LocalSongsProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        src = self.sourceModel()
        index = src.index(source_row, 0, source_parent)
        song = src.data(index, LocalSongsItemRole.SONG)
        artist = src.data(index, LocalSongsItemRole.ARTIST)
        album = src.data(index, LocalSongsItemRole.ALBUM)
        reg_exp = self.filterRegularExpression()
        return reg_exp.match(song).hasMatch() or reg_exp.match(artist).hasMatch() or reg_exp.match(album).hasMatch()

class LocalSongsModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.localsongs = []

    def reload(self):
        self.localsongs = [mp3 for mp3 in localsongs.mp3s]
        self.localsongs = sorted(self.localsongs, key=lambda mp3: mp3.title().lower())

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsEditable | Qt.ItemIsSelectable

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.localsongs)

    def entry(self, row: int):
        return self.localsongs[row]

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()

        row = index.row()

        if row < 0 or row >= self.rowCount():
            return QVariant()

        mp3 = self.localsongs[row]

        if role == LocalSongsItemRole.SONG:
            return mp3.title()

        if role == LocalSongsItemRole.ARTIST:
            if mp3.artist:
                return mp3.artist
            return ""

        if role == LocalSongsItemRole.ALBUM:
            if mp3.album:
                return mp3.album
            return ""

        if role == LocalSongsItemRole.IMAGE:
            return mp3.image

        return QVariant()

    def update_row(self, row, roles=None):
        if row < 0 or row >= self.rowCount():
            return

        index = self.index(row)

        self.dataChanged.emit(index, index, roles or [])

class LocalSongsView(ListProxyView):
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
        self.row_clicked.emit(self._source_index(idx).row())

    def _on_item_double_clicked(self, idx: QModelIndex):
        self.row_double_clicked.emit(self._source_index(idx).row())