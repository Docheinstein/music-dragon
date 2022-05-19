from difflib import get_close_matches
from typing import List, Optional

from PyQt5.QtCore import QRunnable, QTimer, QObject, pyqtSignal, pyqtSlot, QCoreApplication
from PyQt5.QtGui import QFont, QMouseEvent
from PyQt5.QtWidgets import QMainWindow, QLabel, QApplication
from ytmusicapi import YTMusic

import musicbrainz
import repository
import ui.resources
import workers
from log import debug
from musicbrainz import MbReleaseGroup, MbTrack
from ui.preferenceswindow import PreferencesWindow
from repository import Artist, ReleaseGroup, Release, get_artist, \
    get_release_group, get_entity, get_track, get_release
from ui.albumtrackswidget import AlbumTracksModel
from ui.artistalbumswidget import ArtistAlbumsModel
from ui.searchresultswidget import SearchResultsModel
from ui.ui_mainwindow import Ui_MainWindow
from utils import j, make_pixmap_from_data
from youtube import YtDownloader
from youtube import YtTrack

SEARCH_DEBOUNCE_MS = 800

yt: Optional[YTMusic] = None


# ======= FETCH YOUTUBE TRACKS RUNNABLE ===============
# Fetch the youtube videos associated with the tracks
# =====================================================

class FetchYoutubeTracksSignals(QObject):
    track_fetched = pyqtSignal(MbTrack, YtTrack)
    finished = pyqtSignal(MbTrack)

class FetchYoutubeTracksRunnable(QRunnable):
    def __init__(self, tracks: List[MbTrack], album_hint: MbReleaseGroup=None):
        super().__init__()
        self.signals = FetchYoutubeTracksSignals()
        self.tracks = tracks
        self.album_hint = album_hint

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[FetchYoutubeTracksRunnable (tracks={[t.title for t in self.tracks]}])")

        fetched_tracks = {}
        # for t in self.tracks:
        #     tracks_fetch_status[t.title] = False

        # Fetch the video id associated with each track.
        # Before doing many queries, try to fetch the album from youtube and its tracks,
        # since it's likely that the album already contains the tracks we need
        # (if it's not the case something about musicbrainz fetched release
        # or youtube album is incorrect)

        # 1. Fetch artist -> album -> track
        if self.album_hint:
            artist_query = self.album_hint.artists_string()
            album_query = self.album_hint.title

            debug(f"YOUTUBE: search(artists='{artist_query}')")
            artists = yt.search(self.album_hint.artists_string(), filter="artists")
            debug(j(artists))

            closest_artists_name = get_close_matches(artist_query, [artist["artist"] for artist in artists])
            if closest_artists_name:
                closest_artist_name = closest_artists_name[0]
                debug(f"Closest artist found: {closest_artist_name}")
                artist = [a for a in artists if a["artist"] == closest_artist_name][0]

                debug(f"YOUTUBE: get_artist(artist='{artist['browseId']}')")
                artist_details = yt.get_artist(artist["browseId"])
                debug(j(artist_details))

                debug(f"YOUTUBE: get_artist_albums(artist='{artist['browseId']}')")
                if "albums" in artist_details:
                    if "params" in artist_details["albums"]:
                        artist_albums = yt.get_artist_albums(artist["browseId"], artist_details["albums"]["params"])
                        debug(j(artist_albums))

                        closest_albums_name = get_close_matches(album_query, [album["title"] for album in artist_albums])
                        if closest_albums_name:
                            closest_album_name = closest_albums_name[0]
                            debug(f"Closest album found: {closest_album_name}")
                            album = [a for a in artist_albums if a["title"] == closest_album_name][0]

                            debug(f"YOUTUBE: get_album(album='{album['browseId']}')")
                            album_details = yt.get_album(album["browseId"])
                            debug(j(album_details))

                            # Notify only if the mbtrack actually contains the youtube tracks
                            for yttrack in album_details["tracks"]:
                                for mbtrack in self.tracks:
                                    if mbtrack.id not in fetched_tracks: # not fetched yet
                                        # TODO: better heuristic for figure out if the video matches the track
                                        if yttrack["title"].startswith(mbtrack.title):
                                            yttrack["album"] = { # hack track, adding album id
                                                "name": yttrack["album"],
                                                "id": album["browseId"]
                                            }
                                            y = YtTrack(mbtrack, yttrack)
                                            fetched_tracks[mbtrack.id] = y
                                            self.signals.track_fetched.emit(mbtrack, y)
                                            break
                                else:
                                    debug(f"Skipping youtube song '{yttrack['title']}': no match between tracks titles")
                    else:
                        print("WARN: no 'params' key for artist albums")
                else:
                    print("WARN: no 'albums' for artist")

        debug(f"Tracks fetched through album retrieval: {len(fetched_tracks)}/{len(self.tracks)}")
        for t in self.tracks:
            if t.id in fetched_tracks:
                debug(f"FOUND:   {t.title} ({fetched_tracks[t.id].video_title})")
            else:
                debug(f"MISSING: {t.title}")

        # 2. Fetch track directly
        for track in self.tracks:
            if track.id not in fetched_tracks:
                query = track.release.release_group.artists_string() + " " + track.title
                yt_songs = yt.search(query, filter="songs")
                debug(j(yt_songs))
                if yt_songs:
                    y = YtTrack(track, yt_songs[0])
                    fetched_tracks[track.id] = y
                    self.signals.track_fetched.emit(track, y)

        for t in self.tracks:
            if t.id in fetched_tracks:
                debug(f"FOUND:   {t.title} ({fetched_tracks[t.id].video_title})")
            else:
                debug(f"MISSING: {t.title}")

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Pages
        self.pages_stack = []
        self.pages_stack_cursor = -1

        self.ui.homePageButton.clicked.connect(self.on_home_page_button_clicked)
        self.ui.searchPageButton.clicked.connect(self.on_search_page_button_clicked)
        self.ui.downloadsPageButton.clicked.connect(self.on_downloads_page_button_clicked)

        self.pages_buttons = [
            self.ui.homePageButton,
            self.ui.searchPageButton,
            self.ui.downloadsPageButton
        ]
        self.set_search_page()

        self.ui.backButton.clicked.connect(self.on_back_button_clicked)
        self.ui.forwardButton.clicked.connect(self.on_forward_button_clicked)


        # Search
        self.search_results_model = SearchResultsModel()
        self.ui.searchBar.textChanged.connect(self.on_search)

        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self.on_search_debounce_time_elapsed)

        self.ui.searchResults.set_model(self.search_results_model)
        self.ui.searchResults.row_clicked.connect(self.on_search_result_clicked)
        self.ui.searchResults.subtitle_clicked.connect(self.on_search_result_subtitle_clicked)

        self.last_search_query = None


        # Album
        self.current_release_group_id = None
        self.album_tracks_model = AlbumTracksModel()
        self.ui.albumTracks.set_model(self.album_tracks_model)
        self.ui.albumTracks.row_clicked.connect(self.on_album_track_clicked)

        self.ui.albumArtist.set_underline_on_hover(True)
        self.ui.albumArtist.clicked.connect(self.on_album_artist_clicked)

        self.ui.albumCoverPrevButton.clicked.connect(self.on_album_cover_prev_button_clicked)
        self.ui.albumCoverNextButton.clicked.connect(self.on_album_cover_next_button_clicked)

        # self.ui.albumTracks.download_track_clicked.connect(self.on_download_track_clicked)
        # self.ui.albumDownloadAllButton.clicked.connect(self.on_download_album_tracks_clicked)

        # Artist
        self.current_artist_id = None
        self.artist_albums_model = ArtistAlbumsModel()
        self.ui.artistAlbums.set_model(self.artist_albums_model)
        self.ui.artistAlbums.row_clicked.connect(self.on_artist_album_clicked)

        # Menu
        self.ui.actionPreferences.triggered.connect(self.on_action_preferences)

        # Downloader
        # self.downloader = YtDownloader()
        # self.downloader.track_download_started.connect(self.on_track_download_started)
        # self.downloader.track_download_progress.connect(self.on_track_download_progress)
        # self.downloader.track_download_finished.connect(self.on_track_download_finished)

    def set_home_page(self):
        self.push_page(self.ui.homePage)

    def set_search_page(self):
        self.push_page(self.ui.searchPage)

    def set_downloads_page(self):
        self.push_page(self.ui.downloadsPage)

    def set_album_page(self):
        self.push_page(self.ui.albumPage)

    def set_artist_page(self):
        self.push_page(self.ui.artistPage)

    def push_page(self, page):
        self.pages_stack_cursor = self.pages_stack_cursor + 1
        self.pages_stack = self.pages_stack[:self.pages_stack_cursor]
        self.pages_stack.append(page)
        self._update_current_page()

    def prev_page(self):
        self.pages_stack_cursor = self.pages_stack_cursor - 1
        self._update_current_page()

    def next_page(self):
        self.pages_stack_cursor = self.pages_stack_cursor + 1
        self._update_current_page()

    def _update_current_page(self):
        def page_to_string(p):
            if p == self.ui.homePage:
                return "home"
            if p == self.ui.searchPage:
                return "search"
            if p == self.ui.downloadsPage:
                return "downloads"
            if p == self.ui.albumPage:
                return "album"
            if p == self.ui.artistPage:
                return "artist"
        next_page = self.pages_stack[self.pages_stack_cursor]
        debug(f"Updating current page to {page_to_string(next_page)}")
        debug(f"Page stack is ",
            [(f'{page_to_string(p)} (ACTIVE)' if idx == self.pages_stack_cursor else page_to_string(p))
             for idx, p in enumerate(self.pages_stack)])
        self.unselect_pages_buttons()

        if next_page == self.ui.homePage:
            self.select_page_button(self.ui.homePageButton)
        elif next_page == self.ui.searchPage:
            self.select_page_button(self.ui.searchPageButton)
        elif next_page == self.ui.downloadsPage:
            self.select_page_button(self.ui.downloadsPageButton)
        elif next_page == self.ui.albumPage:
            pass
        elif next_page == self.ui.artistPage:
            pass

        self.ui.pages.setCurrentWidget(next_page)

        self.ui.backButton.setEnabled(self.pages_stack_cursor > 0)
        self.ui.forwardButton.setEnabled(self.pages_stack_cursor < len(self.pages_stack) - 1)

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


    def open_release_group(self, release_group: ReleaseGroup):
        if not isinstance(release_group, ReleaseGroup):
            raise TypeError(f"Expected object of type 'ReleaseGroup', found {type(release_group)}")

        self.current_release_group_id = release_group.id

        # title
        self.ui.albumTitle.setText(release_group.title)

        # artist
        self.ui.albumArtist.setText(release_group.artists_string())

        # icon
        cover = release_group.images.preferred_image()
        self.ui.albumCover.setPixmap(make_pixmap_from_data(cover, default=ui.resources.COVER_PLACEHOLDER_PIXMAP))

        # download
        # self.ui.albumDownloadAllButton.setEnabled(False)

        # tracks
        self.album_tracks_model.release_id = None
        self.ui.albumTracks.invalidate()

        # switch page
        self.set_album_page()

        # fetch the main release and its tracks
        repository.fetch_release_group_releases(release_group.id, self.on_release_group_releases_result)


    def open_artist(self, artist: Artist):
        if not isinstance(artist, Artist):
            raise TypeError(f"Expected object of type 'Artist', found {type(artist)}")
        debug(f"open_artist({artist.id})")

        self.current_artist_id = artist.id

        # title
        self.ui.artistName.setText(artist.name)

        # icon
        cover = artist.images.preferred_image()
        self.ui.artistCover.setPixmap(make_pixmap_from_data(cover, default=ui.resources.COVER_PLACEHOLDER_PIXMAP))

        # albums
        self.artist_albums_model.artist_id = artist.id
        self.ui.artistAlbums.invalidate()

        # switch page
        self.set_artist_page()

        # fetch the artist details (e.g. artist release groups)
        repository.fetch_artist(artist.id, self.on_artist_result, self.on_artist_image_result)

    def on_action_preferences(self):
        debug("on_action_preferences")
        preferences_window = PreferencesWindow()
        preferences_window.exec()

    def on_home_page_button_clicked(self, ev: QMouseEvent):
        self.set_home_page()

    def on_search_page_button_clicked(self, ev: QMouseEvent):
        self.set_search_page()

    def on_downloads_page_button_clicked(self, ev: QMouseEvent):
        self.set_downloads_page()

    def on_back_button_clicked(self):
        self.prev_page()

    def on_forward_button_clicked(self):
        self.next_page()

    def on_search(self):
        query = self.ui.searchBar.text()

        if not query:
            return

        debug(f"on_search({query}) [not performed yet]")
        self.search_debounce_timer.start(SEARCH_DEBOUNCE_MS)

    def on_search_debounce_time_elapsed(self):
        query = self.ui.searchBar.text()
        debug(f"on_search_debounce_time_elapsed(query={query})")

        repository.search_release_groups(
            query,
            release_groups_callback=self.on_search_release_groups_result,
            release_group_image_callback=self.on_release_group_image_result,
        )
        repository.search_artists(
            query,
            artists_callback=self.on_search_artists_result,
            artist_image_callback=self.on_artist_image_result,
        )


    def on_search_release_groups_result(self, query, release_groups: List[ReleaseGroup]):
        debug(f"on_search_release_groups_result(query={query}")

        pending_changes = False

        if query != self.last_search_query:
            debug("Clearing search results")
            self.last_search_query = query
            self.search_results_model.results.clear()
            pending_changes = True

        for release_group in release_groups:
            self.search_results_model.results.append(release_group.id)
            pending_changes = True

        if pending_changes:
            self.ui.searchResults.invalidate()


    def on_search_artists_result(self, query, artists: List[Artist]):
        debug(f"on_search_artists_result(query={query}")

        pending_changes = False

        if query != self.last_search_query:
            debug("Clearing search results")
            self.last_search_query = query
            self.search_results_model.results.clear()
            pending_changes = True

        for artist in artists:
            self.search_results_model.results.append(artist.id)
            pending_changes = True

        if pending_changes:
            self.ui.searchResults.invalidate()


    def on_release_group_releases_result(self, release_group_id: str, releases: List[Release]):
        debug(f"on_search_release_group_releases_result(release_group_id={release_group_id})")

        self.album_tracks_model.release_id = get_release_group(release_group_id).main_release_id
        self.ui.albumTracks.invalidate()

        # TODO
        # fetch youtube videos for tracks
        # youtube_track_runnable = FetchYoutubeTracksRunnable(release.tracks)
        # youtube_track_runnable = FetchYoutubeTracksRunnable(release.tracks, album_hint=release.release_group)
        # youtube_track_runnable.signals.track_fetched.connect(self.on_youtube_track_fetched)
        # youtube_track_runnable.signals.finished.connect(self.on_youtube_tracks_fetch_finished)
        # QThreadPool.globalInstance().start(youtube_track_runnable)


    def on_release_group_image_result(self, release_group_id, image):
        debug(f"on_release_group_image_result(release_group_id={release_group_id})")

        self.on_album_cover_update(release_group_id)


    def on_artist_result(self, artist_id, artist: Artist):
        debug(f"on_artist_result(artist_id={artist_id})")

        if self.current_artist_id == artist_id:
            self.ui.artistAlbums.invalidate()

        for rg_id in artist.release_group_ids:
            repository.fetch_release_group_cover(rg_id, self.on_release_group_image_result)

    def on_artist_image_result(self, artist_id, image):
        debug(f"on_artist_image_result(artist_id={artist_id})")

        # search page
        self.ui.searchResults.update_row(artist_id)

        # artist page
        if self.current_artist_id == artist_id:
            image = get_artist(artist_id).images.preferred_image()
            self.ui.artistCover.setPixmap(make_pixmap_from_data(
                image, default=ui.resources.COVER_PLACEHOLDER_PIXMAP)
            )

    def on_search_result_clicked(self, row: int):
        debug(f"on_search_result_clicked({row})")
        result_id = self.search_results_model.results[row]
        result = get_entity(result_id)

        if isinstance(result, ReleaseGroup):
            self.open_release_group(result)
        elif isinstance(result, Artist):
            self.open_artist(result)
        else:
            print("WARN: not supported yet")

    def on_search_result_subtitle_clicked(self, row: int):
        debug(f"on_search_result_subtitle_clicked({row})")

        result_id = self.search_results_model.results[row]
        result = get_entity(result_id)

        if isinstance(result, ReleaseGroup):
            # TODO: what if there is more than an arist?
            # should probably add different labels separated by commasS
            self.open_artist(result.artists()[0])
        elif isinstance(result, Artist):
            print("WARN: wtf?")
        else:
            print("WARN: not supported yet")

    def on_artist_album_clicked(self, row: int):
        debug(f"on_album_artist_clicked(row={row})")
        release_group_id = self.artist_albums_model.entry(row)
        release_group = get_release_group(release_group_id)

        if not release_group:
            print(f"WARN: no release group found for id {release_group_id}")
            return

        self.open_release_group(release_group)

    def on_album_track_clicked(self, row: int):
        track_id = self.album_tracks_model.entry(row)
        track = get_track(track_id)

        if not track:
            print(f"WARN: no release group found for id {track_id}")
            return

    def on_album_artist_clicked(self):
        debug("on_album_artist_clicked")
        release_group = get_release_group(self.current_release_group_id)
        release_group_artists = release_group.artists()
        if not release_group_artists:
            print(f"WARN: no artist found for release group {self.current_release_group_id}")
        # TODO: more than an artist
        self.open_artist(release_group_artists[0])

    def on_album_cover_prev_button_clicked(self):
        debug("on_album_cover_prev_button_clicked")

    def on_album_cover_next_button_clicked(self):
        debug("on_album_cover_next_button_clicked")
        # check if there is still a cover to fetch, otherwise cycle the ones we have
        self.ui.albumCover.setPixmap(ui.resources.COVER_PLACEHOLDER_PIXMAP)
        release_group = get_release_group(self.current_release_group_id)
        release_group_releases = release_group.releases()
        for release in release_group_releases:
            if not release.fetched_front_cover:
                debug(f"Retrieving next front cover: of release {release.id}")
                repository.fetch_release_cover(release.id, self.on_album_cover_change_image_result)
                return
        # cycle
        debug("Every release album has been fetched, cycling between the retrieved ones")
        release_group.images.set_preferred_image_next()
        self.on_album_cover_update(release_group.id)

    def on_album_cover_change_image_result(self, release_id, image):
        debug(f"on_album_cover_change_image_result(release_id={release_id})")

        if not image:
            debug("Going forward")
            self.on_album_cover_next_button_clicked()
            return

        release_group = get_release(release_id).release_group()
        release_group.images.preferred_image_id = release_id

        self.on_album_cover_update(release_group.id)

    def on_album_cover_update(self, release_group_id):

        release_group = get_release_group(release_group_id)

        # search page
        self.ui.searchResults.update_row(release_group.id)

        # album page
        if self.current_release_group_id == release_group.id:
            debug(f"Updating album cover: there are {len(release_group.images.images)} images: {release_group.images}")

            cover = release_group.images.preferred_image()
            self.ui.albumCover.setPixmap(make_pixmap_from_data(
                cover, default=ui.resources.COVER_PLACEHOLDER_PIXMAP)
            )

        # artist page
        self.ui.artistAlbums.update_row(release_group.id)

        # tracks
        self.ui.albumTracks.invalidate()

    # def on_youtube_track_fetched(self, mbtrack: MbTrack, yttrack: YtTrack):
    #     debug(f"on_youtube_track_fetched(track_id={mbtrack.id})")
    #
    #     if not (self.current_release_group and self.current_release_group.id == mbtrack.release.release_group.id):
    #         print("WARN: got youtube track details outside album page")
    #         return
    #
    #     self.ui.albumTracks.set_youtube_track(mbtrack, yttrack)
    #
    #     # for idx, track in enumerate(self.album_model.tracks):
    #     #     if track.id == mbtrack.id:
    #     #         track.youtube_track = yttrack
    #     #         self.album_model.invalidate(idx)
    #
    # def on_youtube_tracks_fetch_finished(self, mbtrack: MbTrack):
    #     debug(f"on_youtube_track_fetched(track_id={mbtrack.id})")
    #
    #     if not (self.current_release_group and self.current_release_group.id == mbtrack.release.release_group.id):
    #         print("WARN: got youtube track details outside album page")
    #         return
    #
    #     self.ui.albumDownloadAllButton.setEnabled(True)

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

    # def on_download_album_tracks_clicked(self):
    #     debug(f"on_download_album_tracks_clicked")
    #     for track in self.ui.albumTracks.tracks:
    #         self.download_track(track)
    #
    # def on_download_track_clicked(self, track: MbTrack):
    #     debug(f"on_download_track_clicked(track_id={track.id})")
    #     self.download_track(track)
    #
    # def download_track(self, mbtrack: MbTrack):
    #     if not mbtrack.youtube_track:
    #         print(f"WARN: no youtube video has been found for track: {mbtrack.title}")
    #         return
    #
    #     self.enqueue_download(mbtrack.youtube_track)
    #     # TODO: show loader instead of download button
    #     self.ui.albumTracks.set_download_enabled(mbtrack, False)
    #
    # def enqueue_download(self, track: YtTrack):
    #     self.downloader.enqueue(track)
    #     self.ui.downloads.add_track(track)

    # def on_album_clicked(self, mb_release_group: MbReleaseGroup):
    #     self.open_release_group(mb_release_group)
    #
    # def on_track_download_started(self, track: YtTrack):
    #     debug(f"on_track_download_started(track={track.mb_track.title})")
    #     self.ui.albumTracks.set_download_progress_visible(track.mb_track, True)
    #     self.ui.albumTracks.set_download_progress(track.mb_track, percentage=0)
    #
    #     self.ui.downloads.set_download_progress_visible(track, True)
    #     self.ui.downloads.set_download_progress(track, percentage=0)
    #
    # def on_track_download_progress(self, track: YtTrack, progress: float):
    #     debug(f"on_track_download_progress(track={track.mb_track.title}, progress={progress})")
    #     self.ui.albumTracks.set_download_progress(track.mb_track, percentage=int(progress))
    #     self.ui.downloads.set_download_progress(track, percentage=int(progress))
    #
    # def on_track_download_finished(self, track: YtTrack):
    #     debug(f"on_track_download_finished(track={track.mb_track.title})")
    #     self.ui.albumTracks.set_download_progress_visible(track.mb_track, False)
    #     self.ui.downloads.remove_track(track)

    #
    # def do_album_download(self, artist_query, album_query):
    #     debug(f"do_album_download(artist={artist_query}, album={album_query})")
    #
    #
    #     # Find artist
    #     result = yt.search(artist_query, filter="artists")
    #     debug(j(result))
    #
    #     artist_found = False
    #     album_found = False
    #
    #     closest_artist_name = get_close_matches(artist_query, [artist["artist"] for artist in result])
    #
    #     if not closest_artist_name:
    #         print(f"WARN: cannot find artist with name {artist_query}")
    #         self.ui.albumDownloadStatus.text("Download failed")
    #         return
    #
    #     closest_artist_name = closest_artist_name[0]
    #
    #     for artist in result:
    #         if artist["artist"] == closest_artist_name:
    #             debug(f"ARTIST FOUND: {artist['browseId']}")
    #             artist_found = True
    #             artist_details = yt.get_artist(artist["browseId"])
    #             artist_albums = yt.get_artist_albums(artist["browseId"], artist_details["albums"]["params"])
    #             debug(j(artist_albums))
    #
    #             closest_album_name = get_close_matches(album_query, [album["title"] for album in artist_albums])
    #
    #             if not closest_album_name:
    #                 print(f"WARN: cannot find album with title {album_query}")
    #                 self.ui.albumDownloadStatus.text("Download failed")
    #                 return
    #
    #             closest_album_name = closest_album_name[0]
    #
    #             for album in artist_albums:
    #                 if album["title"] == closest_album_name:
    #                     debug(f"ALBUM FOUND: {album['browseId']}")
    #                     album_found = True
    #                     album_details = yt.get_album(album["browseId"])
    #                     debug(j(album_details))
    #                     tracks = album_details["tracks"]
    #                     for track in tracks:
    #                         track_name = track["title"]
    #                         duration = track["duration"]
    #                         video_id = track["videoId"]
    #                         debug(f"- {track_name}: {video_id} [{duration}]")
    #
    #                     tracks_downloader = TrackDownloaderRunnable(closest_artist_name, closest_album_name, tracks)
    #                     tracks_downloader.signals.track_download_started.connect(self.on_track_download_started)
    #                     tracks_downloader.signals.track_download_progress.connect(self.on_track_download_progress)
    #                     tracks_downloader.signals.track_download_finished.connect(self.on_track_download_finished)
    #                     QThreadPool.globalInstance().start(tracks_downloader)
    #                     return
    #
    #     if not artist_found:
    #         print(f"WARN: cannot find artist with name {artist_query}")
    #         self.ui.albumDownloadStatus.text("Download failed")
    #         return
    #
    #     if not album_found:
    #         print(f"WARN: cannot find album with title {album_query}")
    #         self.ui.albumDownloadStatus.text("Download failed")
    #         return

    # def on_track_download_started(self, track_name):
    #     print(f"Started download of {track_name}")
    #
    # def on_track_download_progress(self, track_name, progress_str):
    #     self.ui.albumDownloadStatus.setText(f"{track_name}: {progress_str}")
    #
    # def on_track_download_finished(self, track_name):
    #     print(f"Finished download of {track_name}")