import time
from typing import Any

import musicbrainzngs as mb
import asyncio

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QRunnable, QThreadPool, QTimer, QThread, QObject, pyqtSignal, pyqtSlot, QAbstractListModel, \
    QModelIndex, QVariant
from PyQt5.QtGui import QStandardItemModel, QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QItemDelegate, QStyledItemDelegate, QListWidgetItem
from musicbrainzngs import ResponseError

from log import debug
from ui_mainwindow import Ui_MainWindow
from utils import j

SEARCH_DEBOUNCE_MS = 800

# https://www.riverbankcomputing.com/static/Docs/PyQt4/new_style_signals_slots.html#the-pyqtslot-decorator
# https://realpython.com/python-pyqt-qthread/
# https://gist.github.com/ksvbka/1f26ada0c6201c2cf19f59b100d224a9


def make_icon_from_data(data):
    pixmap = QPixmap()
    pixmap.loadFromData(data)
    return QIcon(pixmap)

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
        artists = mb.search_artists(self.query, limit=3)["artist-list"]
        debug(j(artists))

        print(f"search_releases: '{self.query}'")
        releases = mb.search_releases(self.query, limit=3)["release-list"]
        debug(j(releases))

        self.signals.finished.emit(artists, releases)


# class SearchWorker(QObject):
#     finished = pyqtSignal()
#     progress = pyqtSignal(int)
#
#     def __init__(self):
#         super().__init__()
#
#     def run(self):
#         debug("-------------------------------------------------")
#         debug(f"[SearchWorker invoked on thread {QThread.currentThread()}]")


# class ContentItem(QStyledItemDelegate):
#     def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> None:

#
# # https://doc.qt.io/qt-5/model-view-programming.html
# class ContentModel(QAbstractListModel):
#
#     def __init__(self):
#         super().__init__()
#         self.items = []
#
#     def rowCount(self, parent: QModelIndex = ...) -> int:
#         return len(self.items)
#
#     def data(self, index: QModelIndex, role: int = ...) -> Any:
#         if not index.isValid():
#             return QVariant()
#
#         row = index.row()
#
#         if row < 0 or row >= self.rowCount():
#             return QVariant()
#
#         item = self.items[row]
#
#         if role == QtCore.Qt.DecorationRole:
#             print("Asking for DecorationRole")
#             if item.get("image"):
#                 print("Returning Image for DecorationRole")
#                 return item["image"]
#         if role == QtCore.Qt.DisplayRole:
#             if item["type"] == "artist":
#                 return f'{item["name"]} [{item["type"]}]'
#             elif item["type"] == "release":
#                 return f'{item["title"]} [{item["type"]}]'
#
#
#         return QVariant()
#
#
#     def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
#         pass
#

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.searchBar.textChanged.connect(self.on_search)

        # self.search_thread = QThread()
        # self.search_worker = SearchWorker()
        # self.search_worker.moveToThread(self.search_thread)
        # self.search_thread.started.connect(self.search_worker.run)
        # self.search_worker.finished.connect(self.search_thread.quit)
        # self.search_worker.finished.connect(self.search_worker.deleteLater)
        # self.search_thread.finished.connect(self.search_thread.deleteLater)


        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self.on_search_debounce_time_elapsed)


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
        search_runnable.signals.finished.connect(self.on_search_result)

        QThreadPool.globalInstance().start(search_runnable)


    def on_search_result(self, artists, releases):
        debug(f"on_search_finished")

        self.ui.listWidget.clear()

        icon = QIcon("res/questionmark.png")

        # update list
        for artist in artists:
            text = f'{artist["name"]} [Artist]'
            item = QListWidgetItem(icon, text)
            item.setData(QtCore.Qt.UserRole, artist["id"])
            self.ui.listWidget.addItem(item)

        for release in releases:
            if "artist-credit" in release:
                by = ", ".join(credit["name"] for credit in release["artist-credit"])
            else:
                by = "<Unknown>"
            text = f'{release["title"]} [Album by {by}]'
            item = QListWidgetItem(icon, text)
            item.setData(QtCore.Qt.UserRole, release["id"])
            self.ui.listWidget.addItem(item)

        # fetch images
        for release in releases:
            fetch_image_runnable = ImageFetcherRunnable(release["id"])
            fetch_image_runnable.signals.finished.connect(self.on_image_result)
            QThreadPool.globalInstance().start(fetch_image_runnable)

    def on_image_result(self, mbid, image):
        for i in range(self.ui.listWidget.count()):
            item = self.ui.listWidget.item(i)
            item_id = item.data(QtCore.Qt.UserRole)
            if item_id == mbid:
                item.setIcon(make_icon_from_data(image))

