import sys
import time
from difflib import get_close_matches
from enum import Enum
from statistics import mean
from typing import Any, List, Optional

import musicbrainzngs as mb
import asyncio

import youtube_dl
from ytmusicapi import YTMusic

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QRunnable, QThreadPool, QTimer, QThread, QObject, pyqtSignal, pyqtSlot, QAbstractListModel, \
    QModelIndex, QVariant, QRect, Qt, QSize, QPoint
from PyQt5.QtGui import QStandardItemModel, QIcon, QPixmap, QPainter, QBrush, QColor, QFont, QMovie, QMouseEvent
from PyQt5.QtWidgets import QMainWindow, QItemDelegate, QStyledItemDelegate, QListWidgetItem, QLabel, QWidget, \
    QHBoxLayout, QLayout, QSizePolicy, QToolButton, QSpacerItem, QProgressBar, QVBoxLayout, QGridLayout, QPushButton, \
    QListWidget
from musicbrainzngs import ResponseError
from youtube_dl import YoutubeDL

import globals
from cache import COVER_CACHE
from entities import MbReleaseGroup, MbRelease, MbTrack, YtTrack
from log import debug
from preferenceswindow import PreferencesWindow
from ui.ui_mainwindow import Ui_MainWindow
from utils import j, make_icon_from_data, make_pixmap_from_data
SEARCH_DEBOUNCE_MS = 800

yt: Optional[YTMusic] = None

class TrackDownloaderSignals(QObject):
    track_download_started = pyqtSignal(str)
    track_download_progress = pyqtSignal(str, str)
    track_download_finished = pyqtSignal(str)


class TrackDownloaderRunnable(QRunnable):
    def __init__(self, artist: str, album: str, tracks):
        super().__init__()
        self.artist = artist
        self.album = album
        self.tracks = tracks
        self.signals = TrackDownloaderSignals()

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



# ======= SEARCH RELEASE GROUP RUNNABLE ======
# Search the release groups for a given query
# ============================================

class SearchReleaseGroupsSignals(QObject):
    finished = pyqtSignal(str, list)

class SearchReleaseGroupsRunnable(QRunnable):
    def __init__(self, query):
        super().__init__()
        self.signals = SearchReleaseGroupsSignals()
        self.query = query

    @pyqtSlot()
    def run(self) -> None:
        if not self.query:
            return
        debug(f"[SearchReleaseGroupsRunnable (query='{self.query}']")
        #
        # debug(f"MUSICBRAINZ: search_artists: '{self.query}'")
        # artists = mb.search_artists(self.query, limit=8)["artist-list"]
        # debug(j(artists))

        debug(f"MUSICBRAINZ: search_release_groups: '{self.query}'")
        release_group_list = mb.search_release_groups(
            self.query, limit=8, primarytype="Album", status="Official"
        )["release-group-list"]
        debug(j(release_group_list))

        release_groups = [MbReleaseGroup(release_group) for release_group in release_group_list
                          if "primary-type" in release_group and release_group["primary-type"] in ["Album", "EP"]]

        self.signals.finished.emit(self.query, release_groups)


# ======= FETCH RELEASE GROUP COVER RUNNABLE ======
# Fetch the cover of a release group
# =================================================

class FetchReleaseGroupCoverSignals(QObject):
    finished = pyqtSignal(MbReleaseGroup, bytes)


class FetchReleaseGroupCoverRunnable(QRunnable):
    # size can be: “250”, “500”, “1200” or None.
    # If it is None, the largest available picture will be downloaded.
    def __init__(self, release_group: MbReleaseGroup, size="250"):
        super().__init__()
        self.signals = FetchReleaseGroupCoverSignals()
        self.release_group = release_group
        self.size = size

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[SearchReleaseGroupsRunnable (release_group='{self.release_group.title}'], size={self.size})")

        try:
            debug(f"MUSICBRAINZ: get_release_group_image_front: '{self.release_group.id}'")
            data = mb.get_release_group_image_front(self.release_group.id, size=self.size)
            self.signals.finished.emit(self.release_group, data)
        except ResponseError:
            print(f"WARN: no image for release group '{self.release_group.id}'")
            self.signals.finished.emit(self.release_group, bytes())


# ======= FETCH RELEASE GROUP RELEASE RUNNABLE ========
# Fetch the more appropriate release of a release group
# =====================================================

class FetchReleaseGroupMainReleaseSignals(QObject):
    finished = pyqtSignal(MbReleaseGroup, MbRelease)


class FetchReleaseGroupMainReleaseRunnable(QRunnable):
    def __init__(self, release_group: MbReleaseGroup):
        super().__init__()
        self.signals = FetchReleaseGroupMainReleaseSignals()
        self.release_group = release_group

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[FetchReleaseGroupReleaseRunnable (release_group='{self.release_group.title}'])")

        # Fetch all the releases and releases tracks for the release groups
        releases = mb.browse_releases(release_group=self.release_group.id, includes=["recordings"])["release-list"]
        debug(j(releases))

        # Try to figure out which is the more appropriate with heuristics:
        # 1. Take the release with the number of track which is more near
        #    to the average number of tracks of the releases

        tracks_counts = [r["medium-list"][0]["track-count"] for r in releases]
        avg_track_count = mean(tracks_counts)

        deltas = []
        for track_count in tracks_counts:
            deltas.append(abs(track_count - avg_track_count))

        main_release_index = deltas.index(min(deltas))

        debug("tracks_counts", tracks_counts)
        debug("avg_track_count", avg_track_count)
        debug("main_release_index", main_release_index)

        release = MbRelease(self.release_group, releases[main_release_index])
        self.signals.finished.emit(self.release_group, release)



# ======= FETCH YOUTUBE TRACKS RUNNABLE ===============
# Fetch the youtube videos associated with the tracks
# =====================================================

class FetchYoutubeTracksSignals(QObject):
    track_fetched = pyqtSignal(MbTrack, YtTrack)
    finished = pyqtSignal(MbTrack)

class FetchYoutubeTracksRunnable(QRunnable):
    def __init__(self, tracks: List[MbTrack]):
        super().__init__()
        self.signals = FetchYoutubeTracksSignals()
        self.tracks = tracks

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[FetchYoutubeTracksRunnable (tracks={[t.title for t in self.tracks]}])")
        for track in self.tracks:
            query = track.release.release_group.artists_string() + " " + track.title
            yt_songs = yt.search(query, filter="songs")
            debug(j(yt_songs))
            if yt_songs:
                self.signals.track_fetched.emit(track, YtTrack(track, yt_songs[0]))

        self.signals.finished.emit(track)
        # artist_found = False
        # album_found = False
        #
        # closest_artist_name = get_close_matches(artist_query, [artist["artist"] for artist in result])
        #
        # if not closest_artist_name:
        #     print(f"WARN: cannot find artist with name {artist_query}")
        #     self.ui.albumDownloadStatus.text("Download failed")
        #     return
        #
        # closest_artist_name = closest_artist_name[0]
        #
        # for artist in result:
        #     if artist["artist"] == closest_artist_name:
        #         debug(f"ARTIST FOUND: {artist['browseId']}")
        #         artist_found = True
        #         artist_details = yt.get_artist(artist["browseId"])
        #         artist_albums = yt.get_artist_albums(artist["browseId"], artist_details["albums"]["params"])
        #         debug(j(artist_albums))
        #
        #         closest_album_name = get_close_matches(album_query, [album["title"] for album in artist_albums])
        #
        #         if not closest_album_name:
        #             print(f"WARN: cannot find album with title {album_query}")
        #             self.ui.albumDownloadStatus.text("Download failed")
        #             return
        #
        #         closest_album_name = closest_album_name[0]
        #
        #         for album in artist_albums:
        #             if album["title"] == closest_album_name:
        #                 debug(f"ALBUM FOUND: {album['browseId']}")
        #                 album_found = True
        #                 album_details = yt.get_album(album["browseId"])
        #                 debug(j(album_details))
        #                 tracks = album_details["tracks"]
        #                 for track in tracks:
        #                     track_name = track["title"]
        #                     duration = track["duration"]
        #                     video_id = track["videoId"]
        #                     debug(f"- {track_name}: {video_id} [{duration}]")
        #
        #                 tracks_downloader = TrackDownloaderRunnable(closest_artist_name, closest_album_name, tracks)
        #                 tracks_downloader.signals.track_download_started.connect(self.on_track_download_started)
        #                 tracks_downloader.signals.track_download_progress.connect(self.on_track_download_progress)
        #                 tracks_downloader.signals.track_download_finished.connect(self.on_track_download_finished)
        #                 QThreadPool.globalInstance().start(tracks_downloader)
        #                 return
        #
        # if not artist_found:
        #     print(f"WARN: cannot find artist with name {artist_query}")
        #     self.ui.albumDownloadStatus.text("Download failed")
        #     return
        #
        # if not album_found:
        #     print(f"WARN: cannot find album with title {album_query}")
        #     self.ui.albumDownloadStatus.text("Download failed")
        #     return
        #



# ====== ALBUM MODEL =======


#
# class AlbumItemRole:
#     ICON = Qt.DecorationRole
#     TITLE = Qt.DisplayRole
#     YOUTUBE_VIDEO_ID = Qt.UserRole
#
#
# class AlbumItemDelegate(QStyledItemDelegate):
#     def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
#         ICON_TO_TEXT_SPACING = 10
#         DOWNLOAD_ICON_SIZE = 32
#
#         painter.save()
#
#         title: str = index.data(AlbumItemRole.TITLE)
#         icon: QIcon = index.data(AlbumItemRole.ICON)
#         video_id: str = index.data(AlbumItemRole.YOUTUBE_VIDEO_ID)
#
#         main_rect = option.rect
#         x = main_rect.x()
#         y = main_rect.y()
#         w = main_rect.width()
#         h = main_rect.height()
#
#         # Icon
#         icon_size = icon.actualSize(QSize(h, h))
#         icon_rect = QRect(x, y, icon_size.width(), icon_size.height())
#         icon.paint(painter, icon_rect)
#
#         # Title
#         if title:
#             title_rect = QRect(icon_rect.right() + ICON_TO_TEXT_SPACING, y, w - (icon_rect.right() + ICON_TO_TEXT_SPACING), h)
#             # font = painter.font()
#             # font.setBold(True)
#             # font.setPointSize(14)
#             # painter.setFont(font)
#             painter.drawText(title_rect, Qt.AlignVCenter, title)
#
#         # Youtube
#         if video_id:
#             download_icon_rect = QRect(x + w - DOWNLOAD_ICON_SIZE - 10, int(y + (h - DOWNLOAD_ICON_SIZE) / 2), DOWNLOAD_ICON_SIZE, DOWNLOAD_ICON_SIZE)
#             MainWindow.DOWNLOAD_ICON.paint(painter, download_icon_rect)
#             # expected_text_rect: QRect = painter.boundingRect(QRect(), 0, f"[{video_id}]")
#             # video_id_rect = QRect(x + w - expected_text_rect.width() - 16, y, expected_text_rect.width(), h)
#             # painter.drawText(video_id_rect, Qt.AlignVCenter, f"[{video_id}]")
#
#
#         painter.restore()
#
#     def sizeHint(self, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> QSize:
#         return super(AlbumItemDelegate, self).sizeHint(option, index)
#
#     def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> QWidget:
#         debug("createEditor")
#         label = QLabel("Editing")
#         return label
#
#
# class AlbumModel(QAbstractListModel):
#     def __init__(self):
#         super().__init__()
#         self.tracks: List[MbTrack] = []
#
#     def rowCount(self, parent: QModelIndex = ...) -> int:
#         return len(self.tracks)
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
#         track = self.tracks[row]
#
#         if role == AlbumItemRole.TITLE:
#             return track.title
#
#         if role == AlbumItemRole.ICON:
#             cover = track.release.release_group.cover()
#             if cover:
#                 return make_icon_from_data(cover)
#             return MainWindow.DEFAULT_COVER_PLACEHOLDER_ICON
#
#         if role == AlbumItemRole.YOUTUBE_VIDEO_ID:
#             return track.youtube_track.video_id if track.youtube_track else None
#
#         return QVariant()
#
#
#     def invalidate(self, row, roles=None):
#         if row < 0 or row >= self.rowCount():
#             return
#
#         index = self.index(row)
#
#         self.dataChanged.emit(index, index, roles or [])


# ====== SEARCH RESULTS MODEL =======

class SearchResultsItemRole:
    ICON = Qt.DecorationRole
    TITLE = Qt.DisplayRole
    SUBTITLE = Qt.UserRole


class SearchResultsItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        ICON_TO_TEXT_SPACING = 10

        painter.save()

        title: str = index.data(SearchResultsItemRole.TITLE)
        subtitle: str = index.data(SearchResultsItemRole.SUBTITLE)
        icon: QIcon = index.data(SearchResultsItemRole.ICON)

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
        if title:
            title_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING, int(y + h / 2))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(14)
            painter.setFont(font)
            painter.drawText(title_position, title)

        # Subtitle
        if subtitle:
            subtitle_position = QPoint(icon_rect.right() + ICON_TO_TEXT_SPACING, int(y + h / 2 + 20))
            font = painter.font()
            font.setBold(False)
            font.setPointSize(11)
            painter.setFont(font)
            painter.drawText(subtitle_position, subtitle)

        painter.restore()

    def sizeHint(self, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> QSize:
        return super(SearchResultsItemDelegate, self).sizeHint(option, index)


class SearchResultsModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.items: List = []

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.items)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()

        row = index.row()

        if row < 0 or row >= self.rowCount():
            return QVariant()

        item = self.items[row]

        if role == SearchResultsItemRole.TITLE:
            if isinstance(item, MbReleaseGroup):
                return item.title

        if role == SearchResultsItemRole.SUBTITLE:
            if isinstance(item, MbReleaseGroup):
                return item.artists_string()

        if role == SearchResultsItemRole.ICON:
            if isinstance(item, MbReleaseGroup):
                cover = item.cover()
                if cover:
                    return make_icon_from_data(cover)
            return globals.DEFAULT_COVER_PLACEHOLDER_ICON

        return QVariant()

    def invalidate(self, row, roles=None):
        if row < 0 or row >= self.rowCount():
            return

        index = self.index(row)

        self.dataChanged.emit(index, index, roles or [])

# ====== MAIN WINDOW ======

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        globals.DEFAULT_COVER_PLACEHOLDER_ICON = QIcon("res/images/questionmark.png")
        globals.DOWNLOAD_ICON = QIcon("res/images/download.png")

        # Pages

        self.ui.homePageButton.clicked.connect(self.on_home_page_button_clicked)
        self.ui.searchPageButton.clicked.connect(self.on_search_page_button_clicked)
        self.ui.downloadsPageButton.clicked.connect(self.on_downloads_page_button_clicked)

        self.pages_buttons = [
            self.ui.homePageButton,
            self.ui.searchPageButton,
            self.ui.downloadsPageButton
        ]
        self.set_search_page()


        # Search

        self.ui.searchBar.textChanged.connect(self.on_search)

        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self.on_search_debounce_time_elapsed)

        self.search_results_model = SearchResultsModel()

        self.ui.searchResults.setModel(self.search_results_model)
        self.ui.searchResults.setItemDelegate(SearchResultsItemDelegate())
        self.ui.searchResults.clicked.connect(self.on_search_result_clicked)

        self.last_query = None


        # Album
        self.current_release_group: Optional[MbReleaseGroup] = None
        self.ui.albumTracks.download_track_clicked.connect(self.on_download_track_clicked)
        # self.album_model = AlbumModel()
        # self.ui.albumTracks.setModel(self.album_model)
        # self.ui.albumTracks.setItemDelegate(AlbumItemDelegate())
        # self.ui.albumTracks.mouse_pressed.connect(self.on_album_track_mouse_pressed)
        # self.ui.albumTracks.clicked.connect(self.on_album_track_clicked)

        # self.ui.albumYoutubeDownloadButton.clicked.connect(self.on_album_download_clicked)

        # movie = QMovie("res/images/loader.gif")
        # self.ui.albumLoader.setMovie(movie)
        # movie.start()

        # Menu

        self.ui.actionPreferences.triggered.connect(self.on_action_preferences)

    def setup(self):
        global yt
        yt = YTMusic("res/other/yt_auth.json")
        mb.set_useragent("MusicDragon", "0.1")

    def set_home_page(self):
        self.unselect_pages_buttons()
        self.select_page_button(self.ui.homePageButton)
        self.change_page(self.ui.homePage)

    def set_search_page(self):
        self.unselect_pages_buttons()
        self.select_page_button(self.ui.searchPageButton)
        self.change_page(self.ui.searchPage)

    def set_downloads_page(self):
        self.unselect_pages_buttons()
        self.select_page_button(self.ui.downloadsPageButton)
        self.change_page(self.ui.downloadsPage)

    def set_album_page(self):
        self.unselect_pages_buttons()
        self.change_page(self.ui.albumPage)

    def unselect_pages_buttons(self):
        for btn in self.pages_buttons:
            font = btn.font()
            font.setWeight(QFont.Normal)
            btn.setFont(font)
            btn.setStyleSheet("padding: 6px;")

    def select_page_button(self, btn: QLabel):
        font = btn.font()
        font.setWeight(QFont.Bold)
        btn.setFont(font)
        btn.setStyleSheet("padding: 6px; background-color: #565757;")

    def change_page(self, page):
        self.ui.pages.setCurrentWidget(page)

    def open_release_group(self, release_group: MbReleaseGroup):
        if not isinstance(release_group, MbReleaseGroup):
            raise TypeError("Expected object of type 'Release'")

        self.current_release_group = release_group

        # title
        self.ui.albumTitle.setText(release_group.title)

        # artist
        self.ui.albumArtist.setText(release_group.artists_string())

        # icon
        cover = release_group.cover()
        if cover:
            self.ui.albumCover.setPixmap(make_pixmap_from_data(cover))
        else:
            self.ui.albumCover.setPixmap(QPixmap(globals.DEFAULT_COVER_PLACEHOLDER_IMAGE_PATH))

        # tracks
        # self.album_model.beginResetModel()
        # self.album_model.tracks.clear()
        # self.album_model.endResetModel()
        self.ui.albumTracks.clear()

        # download
        self.ui.albumDownloadAllButton.setEnabled(False)

        self.set_album_page()

        # fetch the main release (and its tracks) of the release group
        release_fetcher_runnable = FetchReleaseGroupMainReleaseRunnable(release_group)
        release_fetcher_runnable.signals.finished.connect(self.on_main_release_result)
        QThreadPool.globalInstance().start(release_fetcher_runnable)

    def on_action_preferences(self):
        debug("on_action_preferences")
        preferences_window = PreferencesWindow()
        preferences_window.exec()

    def on_home_page_button_clicked(self):
        self.set_home_page()

    def on_search_page_button_clicked(self):
        self.set_search_page()

    def on_downloads_page_button_clicked(self):
        self.set_downloads_page()

    def on_search(self):
        query = self.ui.searchBar.text()

        if not query:
            return

        debug(f"on_search: '{query}' [not performed yet]")
        self.search_debounce_timer.start(SEARCH_DEBOUNCE_MS)


    def on_search_debounce_time_elapsed(self):
        query = self.ui.searchBar.text()
        debug(f"on_search_debounce_time_elapsed: '{query}'")

        search_release_groups_runnable = SearchReleaseGroupsRunnable(query)
        search_release_groups_runnable.signals.finished.connect(self.on_search_release_groups_finished)

        QThreadPool.globalInstance().start(search_release_groups_runnable)


    def on_search_release_groups_finished(self, query, release_groups: List[MbReleaseGroup]):
        debug(f"on_search_release_groups_finished")

        if query != self.last_query:
            debug("Clearing search results")
            self.last_query = query
            self.search_results_model.beginResetModel()
            self.search_results_model.items.clear()
            self.search_results_model.endResetModel()

        # update model
        self.search_results_model.beginInsertRows(QModelIndex(), self.search_results_model.rowCount(), len(release_groups))

        for release_group in release_groups:
            self.search_results_model.items.append(release_group)

        self.search_results_model.endInsertRows()

        # fetch covers
        for release_group in release_groups:
            if release_group.id not in COVER_CACHE:
                cover_fetcher_runnable = FetchReleaseGroupCoverRunnable(release_group)
                cover_fetcher_runnable.signals.finished.connect(self.on_release_group_cover_fetched)
                QThreadPool.globalInstance().start(cover_fetcher_runnable)


    def on_release_group_cover_fetched(self, release_group: MbReleaseGroup, cover: bytes):
        debug(f"on_release_group_cover_fetched (release_group_id='{release_group.id}'): {'OK' if cover else 'NONE'}")

        COVER_CACHE[release_group.id] = cover

        if self.ui.pages.currentWidget() == self.ui.searchPage:
            for idx, item in enumerate(self.search_results_model.items):
                if isinstance(item, MbReleaseGroup):
                    if item.id == release_group.id:
                        self.search_results_model.invalidate(idx, roles=[SearchResultsItemRole.ICON])
        elif self.ui.pages.currentWidget() == self.ui.albumPage:
            if self.current_release_group and \
                self.current_release_group.id == release_group.id:
                self.ui.albumCover.setPixmap(make_pixmap_from_data(cover))
                # self.album_model.beginResetModel()
                # self.album_model.endResetModel()
                self.ui.albumTracks.set_cover(cover)
        else:
            pass



    def on_search_result_clicked(self, index: QModelIndex):
        item = self.search_results_model.items[index.row()]

        debug(f"on_search_result_clicked on row {index.row()}")

        if isinstance(item, MbReleaseGroup):
            self.open_release_group(item)
        else:
            print("WARN: not supported yet")


    def on_main_release_result(self, release_group: MbReleaseGroup, release: MbRelease):
        debug(f"on_main_release_result(release_group_id={release_group.id})")

        if not (self.current_release_group and self.current_release_group.id == release_group.id):
            print("WARN: got release main release result outside of album page")
            return

        # self.album_model.beginResetModel()
        self.ui.albumTracks.clear()

        for track in release.tracks:
            self.ui.albumTracks.add_track(track)


        # self.album_model.endResetModel()

        # fetch youtube videos for tracks
        # youtube_track_runnable = FetchYoutubeTracksRunnable(release.tracks)
        youtube_track_runnable = FetchYoutubeTracksRunnable(release.tracks[:2])
        youtube_track_runnable.signals.track_fetched.connect(self.on_youtube_track_fetched)
        youtube_track_runnable.signals.finished.connect(self.on_youtube_tracks_fetch_finished)
        QThreadPool.globalInstance().start(youtube_track_runnable)


    def on_youtube_track_fetched(self, mbtrack: MbTrack, yttrack: YtTrack):
        debug(f"on_youtube_track_fetched(track_id={mbtrack.id})")

        if not (self.current_release_group and self.current_release_group.id == mbtrack.release.release_group.id):
            print("WARN: got youtube track details outside album page")
            return

        self.ui.albumTracks.set_youtube_track(mbtrack, yttrack)

        # for idx, track in enumerate(self.album_model.tracks):
        #     if track.id == mbtrack.id:
        #         track.youtube_track = yttrack
        #         self.album_model.invalidate(idx)

    def on_youtube_tracks_fetch_finished(self, mbtrack: MbTrack):
        debug(f"on_youtube_track_fetched(track_id={mbtrack.id})")

        if not (self.current_release_group and self.current_release_group.id == mbtrack.release.release_group.id):
            print("WARN: got youtube track details outside album page")
            return

        self.ui.albumDownloadAllButton.setEnabled(True)

    # def on_album_track_mouse_pressed(self, ev: QMouseEvent):
    #     debug(f"on_album_track_mouse_pressed at x={ev.x()}, y={ev.y()}")

    # def on_album_download_clicked(self):
    #     if self.ui.pages.currentIndex() != ALBUM_PAGE_INDEX:
    #         print("WARN: currently outside of album widget")
    #         return
    #
    #     debug(j(shown_album.release.info))
    #     debug(j(shown_album.release_details))
    #
    #     self.do_album_download(
    #         shown_album.release.info["artist-credit"][0]["name"],
    #         shown_album.release.info["title"])

    def on_download_track_clicked(self, track: MbTrack):
        debug(f"on_download_track_clicked(track_id{track.id})")
        self.ui.albumTracks.set_download_progress_visible(track, True)
        self.ui.albumTracks.set_download_progress(track, 20)



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

                        tracks_downloader = TrackDownloaderRunnable(closest_artist_name, closest_album_name, tracks)
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

