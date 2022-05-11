import sys
import time
from difflib import get_close_matches
from enum import Enum
from typing import Any, List, Optional

import musicbrainzngs as mb
import asyncio

import youtube_dl
from ytmusicapi import YTMusic

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QRunnable, QThreadPool, QTimer, QThread, QObject, pyqtSignal, pyqtSlot, QAbstractListModel, \
    QModelIndex, QVariant, QRect, Qt, QSize, QPoint
from PyQt5.QtGui import QStandardItemModel, QIcon, QPixmap, QPainter, QBrush, QColor, QFont
from PyQt5.QtWidgets import QMainWindow, QItemDelegate, QStyledItemDelegate, QListWidgetItem
from musicbrainzngs import ResponseError
from youtube_dl import YoutubeDL

from log import debug
from ui_mainwindow import Ui_MainWindow
from utils import j

SEARCH_DEBOUNCE_MS = 800
DEFAULT_PLACEHOLDER_IMAGE = "res/questionmark.png"

HOME_WIDGET_INDEX = 0
ALBUM_WIDGET_INDEX = 1

yt: Optional[YTMusic] = None

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

class Track(MBEntity):
    def __init__(self, info):
        super().__init__(info)

track_in_download = None

class ShownAlbum:
    def __init__(self):
        self.release: Optional[Release] = None
        self.release_details = None


shown_album = ShownAlbum()

def qrect_to_string(rect: QRect):
    return f"left={rect.left()} top={rect.top()} right={rect.left() + rect.width()} bottom={rect.top() + rect.height()}"

def make_pixmap_from_data(data):
    pixmap = QPixmap()
    if data:
        pixmap.loadFromData(data)
    return pixmap

def make_icon_from_data(data):
    return QIcon(make_pixmap_from_data(data))



class TracksDownloaderSignals(QObject):
    track_download_started = pyqtSignal(str)
    track_download_progress = pyqtSignal(str, str)
    track_download_finished = pyqtSignal(str)


class TracksDownloaderRunnable(QRunnable):
    def __init__(self, artist, album, tracks):
        super().__init__()
        self.artist = artist
        self.album = album
        self.tracks = tracks
        self.signals = TracksDownloaderSignals()

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[TrackDownloaderRunnable]")
        debug("-----------------------")

        for track in self.tracks:
            track_name = track["title"]
            duration = track["duration"]
            video_id = track["videoId"]

            self.signals.track_download_started.emit(track_name)

            debug(f"Going to download {track_name} at {video_id}")

            class YoutubeDLLogger(object):
                def debug(self, msg):
                    debug(msg)

                def warning(self, msg):
                    print(f"WARN: {msg}")

                def error(self, msg):
                    print(f"ERROR: {msg}", file=sys.stderr)

            def progress_hook(d):
                if "_percent_str" in d:
                    self.signals.track_download_progress.emit(track_name, d["_percent_str"])

                # if d['status'] == 'finished':
                #     self.signals.finished.emit()

            # https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L141
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'logger': YoutubeDLLogger(),
                'progress_hooks': [progress_hook],
                'outtmpl': f"~/Temp/music/down/{self.artist}/%(title)s.%(ext)s"
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f'https://youtube.com/watch?v={video_id}'])

            self.signals.track_download_finished.emit(track_name)



class ReleaseFetcherSignals(QObject):
    finished = pyqtSignal(dict)


class ReleaseFetcherRunnable(QRunnable):
    def __init__(self, mbid):
        super().__init__()
        self.mbid = mbid
        self.signals = ReleaseFetcherSignals()

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[ReleaseFetcherRunnable]")
        debug(f"MBID: '{self.mbid}'")
        debug("-----------------------")

        # release_group = mb.get_release_group_by_id(self.mbid, includes=["releases"])
        # debug(j(release_group))
        # exit(0)
        release = mb.get_release_by_id(self.mbid, includes=["recordings"])

        self.signals.finished.emit(release["release"])




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
            data = mb.get_release_group_image_front(self.mbid, size="250")
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
        artists = mb.search_artists(self.query, limit=8)["artist-list"]
        debug(j(artists))

        print(f"search_releases: '{self.query}'")
        releases = mb.search_release_groups(self.query, limit=8, primarytype="Album", status="Official")["release-group-list"]
        releases = [release for release in releases if release["primary-type"] in ["Album", "EP"]]
        debug(j(releases))

        self.signals.finished.emit(artists, releases)


class ContentItemRole:
    ICON = Qt.DecorationRole
    TITLE = Qt.DisplayRole
    SUBTITLE = Qt.UserRole

class AlbumItemRole:
    ICON = Qt.DecorationRole
    TITLE = Qt.DisplayRole


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
        return super(ContentItemDelegate, self).sizeHint(option, index)


class AlbumItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        ICON_TO_TEXT_SPACING = 10
        # super(ContentItemDelegate, self).paint(painter, option, index)

        row = index.row()
        title: str = index.data(AlbumItemRole.TITLE)
        icon: QIcon = index.data(AlbumItemRole.ICON)

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
        title_rect = QRect(icon_rect.right() + ICON_TO_TEXT_SPACING, y, w - (icon_rect.right() + ICON_TO_TEXT_SPACING), h)
        # font = painter.font()
        # font.setBold(True)
        # font.setPointSize(14)
        # painter.setFont(font)
        painter.drawText(title_rect, Qt.AlignVCenter, title)

        painter.restore()

    def sizeHint(self, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> QSize:
        return super(AlbumItemDelegate, self).sizeHint(option, index)


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
            return QIcon(DEFAULT_PLACEHOLDER_IMAGE)

        return QVariant()



class AlbumModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.tracks: List[Track] = []

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.tracks)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()

        row = index.row()

        if row < 0 or row >= self.rowCount():
            return QVariant()

        track = self.tracks[row]

        if role == AlbumItemRole.TITLE:
            return track.info["recording"]["title"]

        if role == AlbumItemRole.ICON:
            if track.image:
                return make_icon_from_data(track.image)
            return QIcon(DEFAULT_PLACEHOLDER_IMAGE)

        return QVariant()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.searchBar.textChanged.connect(self.on_search)

        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self.on_search_debounce_time_elapsed)

        # Content
        self.content_model = ContentModel()
        self.content_item_delegate = ContentItemDelegate()

        self.ui.searchResults.setModel(self.content_model)
        self.ui.searchResults.setItemDelegate(self.content_item_delegate)
        self.ui.searchResults.clicked.connect(self.on_search_result_clicked)

        # Album
        self.ui.albumBackButton.clicked.connect(self.on_go_home)

        self.album_model = AlbumModel()
        self.album_item_delegate = AlbumItemDelegate()
        self.ui.albumSongs.setModel(self.album_model)
        self.ui.albumSongs.setItemDelegate(self.album_item_delegate)

        self.ui.albumDownloadButton.clicked.connect(self.on_album_download_clicked)


        self.query = None

    def setup(self):
        global yt
        yt = YTMusic("res/yt_auth.json")
        mb.set_useragent("MusicDragon", "0.1")

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
            self.open_release(item)
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

    def open_release(self, release: Release):
        if not isinstance(release, Release):
            raise TypeError("Expected object of type 'Release'")

        shown_album.release = release

        # Title
        self.ui.albumTitle.setText(release.info["title"])

        # Icon
        if release.image:
            self.ui.albumIcon.setPixmap(make_pixmap_from_data(release.image))
        else:
            self.ui.albumIcon.setPixmap(QPixmap(DEFAULT_PLACEHOLDER_IMAGE))

        self.ui.stack.setCurrentWidget(self.ui.albumWidget)


        # Fetch the details of a release
        release_id = release.info["release-list"][0]["id"]
        release_fetcher_runnable = ReleaseFetcherRunnable(release_id)
        release_fetcher_runnable.signals.finished.connect(self.on_release_result)
        QThreadPool.globalInstance().start(release_fetcher_runnable)


    def on_release_result(self, release_details):
        debug(f"on_release_result")
        debug(j(release_details))

        if self.ui.stack.currentIndex() != ALBUM_WIDGET_INDEX:
            print("WARN: got release result but currently outside of album widget")
            return

        shown_album.release_details = release_details

        self.album_model.beginResetModel()
        if len(release_details["medium-list"]) > 1:
            print("WARN: len(medium-list) > 1")
        for t in release_details["medium-list"][0]["track-list"]:
            track = Track(t)
            track.image = shown_album.release.image
            self.album_model.tracks.append(track)
        self.album_model.endResetModel()

    def on_album_download_clicked(self):
        if self.ui.stack.currentIndex() != ALBUM_WIDGET_INDEX:
            print("WARN: currently outside of album widget")
            return

        debug(j(shown_album.release.info))
        debug(j(shown_album.release_details))

        self.do_album_download(
            shown_album.release.info["artist-credit"][0]["name"],
            shown_album.release.info["title"])

    def do_album_download(self, artist_query, album_query):
        debug(f"do_album_download(artist={artist_query}, album={album_query})")


        # Find artist
        result = yt.search(artist_query, filter="artists")
        debug(j(result))

        artist_found = False
        album_found = False

        closest_artist_name = get_close_matches(artist_query, [artist["artist"] for artist in result])

        if not closest_artist_name:
            print(f"WARN: cannot find artist with name {artist_query}")
            self.ui.albumDownloadStatus.text("Download failed")
            return

        closest_artist_name = closest_artist_name[0]

        for artist in result:
            if artist["artist"] == closest_artist_name:
                debug(f"ARTIST FOUND: {artist['browseId']}")
                artist_found = True
                artist_details = yt.get_artist(artist["browseId"])
                artist_albums = yt.get_artist_albums(artist["browseId"], artist_details["albums"]["params"])
                debug(j(artist_albums))

                closest_album_name = get_close_matches(album_query, [album["title"] for album in artist_albums])

                if not closest_album_name:
                    print(f"WARN: cannot find album with title {album_query}")
                    self.ui.albumDownloadStatus.text("Download failed")
                    return

                closest_album_name = closest_album_name[0]

                for album in artist_albums:
                    if album["title"] == closest_album_name:
                        debug(f"ALBUM FOUND: {album['browseId']}")
                        album_found = True
                        album_details = yt.get_album(album["browseId"])
                        debug(j(album_details))
                        tracks = album_details["tracks"]
                        for track in tracks:
                            track_name = track["title"]
                            duration = track["duration"]
                            video_id = track["videoId"]
                            debug(f"- {track_name}: {video_id} [{duration}]")

                        tracks_downloader = TracksDownloaderRunnable(closest_artist_name, closest_album_name, tracks)
                        tracks_downloader.signals.track_download_started.connect(self.on_track_download_started)
                        tracks_downloader.signals.track_download_progress.connect(self.on_track_download_progress)
                        tracks_downloader.signals.track_download_finished.connect(self.on_track_download_finished)
                        QThreadPool.globalInstance().start(tracks_downloader)
                        return

        if not artist_found:
            print(f"WARN: cannot find artist with name {artist_query}")
            self.ui.albumDownloadStatus.text("Download failed")
            return

        if not album_found:
            print(f"WARN: cannot find album with title {album_query}")
            self.ui.albumDownloadStatus.text("Download failed")
            return

    def on_track_download_started(self, track_name):
        print(f"Started download of {track_name}")

    def on_track_download_progress(self, track_name, progress_str):
        self.ui.albumDownloadStatus.setText(f"{track_name}: {progress_str}")

    def on_track_download_finished(self, track_name):
        print(f"Finished download of {track_name}")

