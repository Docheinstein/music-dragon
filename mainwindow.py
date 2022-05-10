import time
from enum import Enum
from typing import Any, List

import musicbrainzngs as mb
import asyncio

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QRunnable, QThreadPool, QTimer, QThread, QObject, pyqtSignal, pyqtSlot, QAbstractListModel, \
    QModelIndex, QVariant, QRect, Qt, QSize, QPoint
from PyQt5.QtGui import QStandardItemModel, QIcon, QPixmap, QPainter, QBrush, QColor, QFont
from PyQt5.QtWidgets import QMainWindow, QItemDelegate, QStyledItemDelegate, QListWidgetItem
from musicbrainzngs import ResponseError

from log import debug
from ui_mainwindow import Ui_MainWindow
from utils import j

SEARCH_DEBOUNCE_MS = 800
DEFAULT_PROXY_IMAGE = "res/questionmark.png"

# https://www.riverbankcomputing.com/static/Docs/PyQt4/new_style_signals_slots.html#the-pyqtslot-decorator
# https://realpython.com/python-pyqt-qthread/
# https://gist.github.com/ksvbka/1f26ada0c6201c2cf19f59b100d224a9


class MBEntity:
    def __init__(self, info):
        self.info = info
        self.image = None

class Artist(MBEntity):
    def __init__(self, info):
        super().__init__(info)

class Release(MBEntity):
    def __init__(self, info):
        super().__init__(info)

def qrect_to_string(rect: QRect):
    return f"left={rect.left()} top={rect.top()} right={rect.left() + rect.width()} bottom={rect.top() + rect.height()}"

def make_pixmap_from_data(data):
    pixmap = QPixmap()
    if data:
        pixmap.loadFromData(data)
    return pixmap

def make_icon_from_data(data):
    return QIcon(make_pixmap_from_data(data))

class ImageFetcherSignals(QObject):
    finished = pyqtSignal(str, bytes)


class ImageFetcherRunnable(QRunnable):
    def __init__(self, mbid, mbtype="release"):
        super().__init__()
        self.mbid = mbid
        self.mbtype = mbtype
        self.signals = ImageFetcherSignals()

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[ImageFetcherRunnable]")
        debug(f"Type: '{self.mbtype}'")
        debug(f"MBID: '{self.mbid}'")
        debug("-----------------------")

        if self.mbtype != "release":
            print("WARN: not supported")
            return

        try:
            print(f"get_image_front: '{self.mbid}'")
            data = mb.get_image_front(self.mbid)
            print(f"get_image_front: '{self.mbid}' OK")
            self.signals.finished.emit(self.mbid, data)
        except ResponseError:
            print(f"WARN: no image for {self.mbid}")



class SearchSignals(QObject):
    finished = pyqtSignal(list, list)

class SearchRunnable(QRunnable):
    def __init__(self, query):
        super().__init__()
        self.query = query
        self.signals = SearchSignals()

    @pyqtSlot()
    def run(self) -> None:
        if not self.query:
            return
        debug(f"[SearchRunnable]")
        debug(f"Search: '{self.query}'")
        debug("-----------------------")

        print(f"search_artists: '{self.query}'")
        artists = mb.search_artists(self.query, limit=2)["artist-list"]
        debug(j(artists))

        print(f"search_releases: '{self.query}'")
        releases = mb.search_releases(self.query, limit=2)["release-list"]
        debug(j(releases))

        self.signals.finished.emit(artists, releases)


class ContentItemRole:
    ICON = Qt.DecorationRole
    TITLE = Qt.DisplayRole
    SUBTITLE = Qt.UserRole


class ContentItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        ICON_TO_TEXT_SPACING = 10
        # super(ContentItemDelegate, self).paint(painter, option, index)

        row = index.row()
        title: str = index.data(ContentItemRole.TITLE)
        subtitle: str = index.data(ContentItemRole.SUBTITLE)
        icon: QIcon = index.data(ContentItemRole.ICON)

        # self.initStyleOption(option, index)

        painter.save()

        # Main
        main_rect = option.rect
        x = main_rect.x()
        y = main_rect.y()
        w = main_rect.width()
        h = main_rect.height()

        # Icon
        icon_size = icon.actualSize(QSize(h, h))
        icon_rect = QRect(x, y, icon_size.width(), icon_size.height())
        icon.paint(painter, icon_rect)

        # Title
        title_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING, int(y + h / 2))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(title_position, title)

        # Subtitle
        subtitle_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING, int(y + h / 2 + 20))
        font = painter.font()
        font.setBold(False)
        font.setPointSize(11)
        painter.setFont(font)
        painter.drawText(subtitle_position, subtitle)

        painter.restore()

    def sizeHint(self, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> QSize:
        # return QSize(400, 80)
        return super(ContentItemDelegate, self).sizeHint(option, index)


# # https://doc.qt.io/qt-5/model-view-programming.html
class ContentModel(QAbstractListModel):

    def __init__(self):
        super().__init__()
        self.items: List[MBEntity] = []

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.items)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()

        row = index.row()

        if row < 0 or row >= self.rowCount():
            return QVariant()

        item = self.items[row]

        if role == ContentItemRole.TITLE:
            if isinstance(item, Artist):
                return f'{item.info["name"]}'
            if isinstance(item, Release):
                return f'{item.info["title"]}'

        if role == ContentItemRole.SUBTITLE:
            if isinstance(item, Artist):
                return "Artist"

            if isinstance(item, Release):
                if "artist-credit" in item.info:
                    by = ", ".join(credit["name"] for credit in item.info["artist-credit"])
                else:
                    by = "Unknown"
                return by

        if role == ContentItemRole.ICON:
            if item.image:
                return make_icon_from_data(item.image)
            return QIcon(DEFAULT_PROXY_IMAGE)

        return QVariant()


#     def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
#         pass
#

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.searchBar.textChanged.connect(self.on_search)

        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self.on_search_debounce_time_elapsed)

        self.content_model = ContentModel()
        self.content_item_delegate = ContentItemDelegate()

        self.ui.searchResults.setModel(self.content_model)
        self.ui.searchResults.setItemDelegate(self.content_item_delegate)
        self.ui.searchResults.clicked.connect(self.on_search_result_clicked)

        self.ui.albumBackButton.clicked.connect(self.on_go_home)

        self.query = None


    def on_search(self):
        self.query = self.ui.searchBar.text()

        if not self.query:
            return

        debug(f"on_search: '{self.query}' [not performed yet]")
        self.search_debounce_timer.start(SEARCH_DEBOUNCE_MS)


    def on_search_debounce_time_elapsed(self):
        debug(f"on_search_debounce_time_elapsed: '{self.query}'")
        # self.search_thread.start()

        search_runnable = SearchRunnable(self.query)
        search_runnable.signals.finished.connect(self.on_search_finished)

        QThreadPool.globalInstance().start(search_runnable)


    def on_search_finished(self, artists, releases):
        debug(f"on_search_finished")

        self.content_model.beginResetModel()
        self.content_model.items = []

        # update model
        for artist in artists:
            self.content_model.items.append(Artist(artist))

        for release in releases:
            self.content_model.items.append(Release(release))

        self.content_model.endResetModel()

        # fetch images
        for release in releases:
            fetch_image_runnable = ImageFetcherRunnable(release["id"])
            fetch_image_runnable.signals.finished.connect(self.on_image_result)
            QThreadPool.globalInstance().start(fetch_image_runnable)


    def on_search_result_clicked(self, index: QModelIndex):
        item = self.content_model.items[index.row()]
        debug(f"on_search_result_clicked on row {index.row()}: '{item.info['id']}'")

        if isinstance(item, Release):
            # Title
            self.ui.albumTitle.setText(item.info["title"])

            # Icon
            if item.image:
                self.ui.albumIcon.setPixmap(make_pixmap_from_data(item.image))
            else:
                self.ui.albumIcon.setPixmap(QPixmap(DEFAULT_PROXY_IMAGE))

            self.ui.stack.setCurrentWidget(self.ui.albumWidget)

        else:
            print("WARN: not supported yet")


    def on_image_result(self, mbid, image):
        for idx, item in enumerate(self.content_model.items):
            if item.info["id"] == mbid:
                self.content_model.beginRemoveRows(QModelIndex(), idx, idx)
                item.image = image
                self.content_model.beginInsertRows(QModelIndex(), idx, idx)

    def on_go_home(self):
        self.ui.stack.setCurrentWidget(self.ui.searchWidget)