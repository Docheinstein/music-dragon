from typing import Any, Optional

from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QModelIndex, QAbstractListModel, QVariant, pyqtSignal, \
    QSortFilterProxyModel, QRectF
from PyQt5.QtGui import QPainter, QMouseEvent
from PyQt5.QtWidgets import QStyledItemDelegate, QListView, QWidget, QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout, \
    QSpacerItem, QGridLayout, QPushButton

from music_dragon import localsongs, favourites, UNKNOWN_ARTIST
from music_dragon.localsongs import Mp3
from music_dragon.log import debug
from music_dragon.ui import resources
from music_dragon.ui.listproxyview import ListProxyView
from music_dragon.utils import make_icon_from_data

class LocalArtistsItemRole:
    NAME = Qt.DisplayRole
    IMAGE = Qt.DecorationRole


class LocalArtistsItemWidget(QWidget):
    favourite_clicked = pyqtSignal(QModelIndex)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.name: Optional[QLabel] = None
            self.fav: Optional[QPushButton] = None

    def __init__(self, parent, index, row, name, image):
        super().__init__(parent)

        self.index = index
        self.row = row
        self.name = name
        self.image = image

        self.ui = LocalArtistsItemWidget.Ui()
        self.setup()
        self.setAutoFillBackground(True)
        self.invalidate()


    def setup(self):
        # artist
        self.ui.name = QLabel()
        f = self.ui.name.font()
        self.ui.name.setFont(f)
        self.ui.name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.ui.name.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # fav
        self.ui.fav = QPushButton()
        self.ui.fav.setIcon(resources.UNFAVOURITE_ICON)
        self.ui.fav.setIconSize(QSize(24, 24))
        self.ui.fav.setFlat(True)
        self.ui.fav.clicked.connect(self._on_fav_clicked)

        # build
        layout = QHBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.addWidget(self.ui.name)
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(self.ui.fav)

        self.setLayout(layout)

    def invalidate(self):
        # artist
        self.ui.name.setText(self.name)

        # fav
        self.ui.fav.setIcon(resources.FAVOURITE_ICON
                            if favourites.is_favourite(artist=self.name)
                            else resources.UNFAVOURITE_ICON)


    def sizeHint(self) -> QSize:
        sz = super().sizeHint()
        return QSize(sz.width(), 48)

    def _on_fav_clicked(self):
        debug(f"_on_fav_clicked({self.name})")
        self.favourite_clicked.emit(self.index)
        self.invalidate()

class LocalArtistsItemDelegate(QStyledItemDelegate):
    favourite_clicked = pyqtSignal(int)

    def __init__(self, proxy: Optional[QSortFilterProxyModel] = None):
        super().__init__()
        self.proxy = proxy

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

        # Icon
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

        # Fav
        source = QRectF(0, 0, 48, 48)
        target = QRectF(w - 24, y + h / 2 - 12, 24, 24)
        painter.drawPixmap(target, resources.FAVOURITE_PIXMAP
                            if favourites.is_favourite(artist=name)
                            else resources.UNFAVOURITE_PIXMAP, source)

        painter.restore()

    def sizeHint(self, option: 'QStyleOptionViewItem', index: QModelIndex) -> QSize:
        sz = super(LocalArtistsItemDelegate, self).sizeHint(option, index)
        return QSize(sz.width(), 48)

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> QWidget:
        name: str = index.data(LocalArtistsItemRole.NAME)
        image: bytes = index.data(LocalArtistsItemRole.IMAGE)

        debug(f"Create editor for row with (artist={name})")
        editor = LocalArtistsItemWidget(parent=parent, index=index, row=index.row(), name=name, image=image)

        editor.favourite_clicked.connect(self._on_favourite_clicked)
        editor.adjustSize()
        return editor

    def updateEditorGeometry(self, editor: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        # debug("updateEditorGeometry")
        rect = option.rect
        rect.setX(rect.x() + 48)
        rect.setY(rect.y())
        editor.setGeometry(rect)

    def _on_favourite_clicked(self, index: QModelIndex):
        index = self.proxy.mapToSource(index) if self.proxy else index
        row = index.row()
        debug(f"_on_favourite_clicked at row {row}")
        self.favourite_clicked.emit(row)

class LocalArtistsProxyModel(QSortFilterProxyModel):
    pass

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
            if not mp3.artist and (UNKNOWN_ARTIST not in mp3s_by_artists or is_better(mp3, mp3s_by_artists[UNKNOWN_ARTIST])):
                mp3s_by_artists[UNKNOWN_ARTIST] = mp3
            if mp3.artist and (mp3.artist not in mp3s_by_artists or is_better(mp3, mp3s_by_artists[mp3.artist])):
                mp3s_by_artists[mp3.artist] = mp3


        self.localartists = list(mp3s_by_artists.values())
        self.localartists = sorted(self.localartists, key=lambda mp3: (mp3.artist or "ZZZZZZZZZZZZZZZZZZZZZZZ").lower()) # TODO: better way

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
            return artist_name or UNKNOWN_ARTIST

        if role == LocalArtistsItemRole.IMAGE:
            return mp3_group.image

        return QVariant()

    def update_row(self, row, roles=None):
        if row < 0 or row >= self.rowCount():
            return

        index = self.index(row)

        self.dataChanged.emit(index, index, roles or [])

class LocalArtistsView(ListProxyView):
    row_clicked = pyqtSignal(int)
    # row_double_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit_index = None
        self.setMouseTracking(True)
        self.clicked.connect(self._on_item_clicked)
        # self.doubleClicked.connect(self._on_item_double_clicked)

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

    # def _on_item_double_clicked(self, idx: QModelIndex):
    #     self.row_double_clicked.emit(idx.row())