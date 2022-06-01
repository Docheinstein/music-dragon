from pathlib import Path
from typing import List

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QMouseEvent
from PyQt5.QtWidgets import QMainWindow, QLabel, QMessageBox
from music_dragon import localsongs, repository, workers, ytcommons, ytdownloader, preferences
from music_dragon.localsongs import Mp3
from music_dragon.log import debug
from music_dragon.repository import Artist, ReleaseGroup, Release, Track, get_artist, \
    get_release_group, get_entity, get_track, get_release, get_youtube_track
from music_dragon.ui import resources
from music_dragon.ui.albumtrackswidget import AlbumTracksModel
from music_dragon.ui.artistalbumswidget import ArtistAlbumsModel
from music_dragon.ui.downloadswidget import DownloadsModel, FinishedDownloadsModel
from music_dragon.ui.imagepreviewwindow import ImagePreviewWindow
from music_dragon.ui.localalbumsview import LocalAlbumsModel, LocalAlbumsItemDelegate
from music_dragon.ui.localartistsview import LocalArtistsModel, LocalArtistsItemDelegate
from music_dragon.ui.localsongsview import LocalSongsModel, LocalSongsItemDelegate
from music_dragon.ui.preferenceswindow import PreferencesWindow
from music_dragon.ui.searchresultswidget import SearchResultsModel
from music_dragon.ui.ui_mainwindow import Ui_MainWindow
from music_dragon.utils import make_pixmap_from_data, open_url, open_folder, is_dark_mode, millis_to_human_string
from music_dragon.ytmusic import YtTrack

SEARCH_DEBOUNCE_MS = 800

DOWNLOADS_TABS_QUEUED_INDEX = 0
DOWNLOADS_TABS_COMPLETED_INDEX = 1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.dark_mode = is_dark_mode()

        # Pages
        self.pages_stack = []
        self.pages_stack_cursor = -1

        self.ui.localPageButton.clicked.connect(self.on_local_page_button_clicked)
        self.ui.searchPageButton.clicked.connect(self.on_search_page_button_clicked)
        self.ui.downloadsPageButton.clicked.connect(self.on_downloads_page_button_clicked)

        self.pages_buttons = [
            self.ui.localPageButton,
            self.ui.searchPageButton,
            self.ui.downloadsPageButton
        ]
        # self.set_local_page()
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
        self.ui.searchResults.subtitle_first_clicked.connect(self.on_search_result_subtitle_first_clicked)
        self.ui.searchResults.subtitle_second_clicked.connect(self.on_search_result_subtitle_second_clicked)

        self.last_search_query = None


        # Album
        self.current_release_group_id = None
        self.album_tracks_model = AlbumTracksModel()
        self.ui.albumTracks.set_model(self.album_tracks_model)
        self.ui.albumTracks.row_clicked.connect(self.on_album_track_clicked)

        self.ui.albumArtist.set_underline_on_hover(True)
        self.ui.albumArtist.clicked.connect(self.on_album_artist_clicked)

        self.ui.albumCover.double_clicked.connect(self.on_album_cover_double_clicked)
        self.ui.albumCover.set_clickable(False)
        self.ui.albumCover.set_double_clickable(True)
        self.album_cover_data = None
        self.ui.albumCoverPrevButton.clicked.connect(self.on_album_cover_prev_button_clicked)
        self.ui.albumCoverNextButton.clicked.connect(self.on_album_cover_next_button_clicked)
        self.album_change_cover_empty_image_callback = None

        self.ui.albumTracks.download_button_clicked.connect(self.on_track_download_button_clicked)
        self.ui.albumTracks.open_video_button_clicked.connect(self.on_track_open_video_button_clicked)
        self.ui.albumDownloadAllButton.clicked.connect(self.on_download_missing_album_tracks_clicked)

        # Artist
        self.current_artist_id = None
        self.artist_albums_model = ArtistAlbumsModel()
        self.ui.artistAlbums.set_model(self.artist_albums_model)
        self.ui.artistAlbums.row_clicked.connect(self.on_artist_album_clicked)
        self.ui.artistCover.double_clicked.connect(self.on_artist_image_double_clicked)
        self.artist_cover_data = None

        # Menu
        self.ui.actionPreferences.triggered.connect(self.on_action_preferences)
        self.ui.actionReload.triggered.connect(self.on_action_reload)

        # Queued ownloads
        self.downloads_model = DownloadsModel()
        self.ui.queuedDownloads.set_model(self.downloads_model)
        self.ui.queuedDownloads.cancel_button_clicked.connect(self.on_download_cancel_button_clicked)
        self.ui.queuedDownloads.artist_clicked.connect(self.on_download_artist_clicked)
        self.ui.queuedDownloads.album_clicked.connect(self.on_download_album_clicked)

        # Completed downloads
        self.finished_downloads_model = FinishedDownloadsModel()
        self.ui.finishedDownloads.set_model(self.finished_downloads_model)
        self.ui.finishedDownloads.artist_clicked.connect(self.on_finished_download_artist_clicked)
        self.ui.finishedDownloads.album_clicked.connect(self.on_finished_download_album_clicked)
        self.ui.finishedDownloads.row_double_clicked.connect(self.on_finished_download_double_clicked)

        # Manual download
        self.ui.manualDownloadButton.clicked.connect(self.on_manual_download_button_clicked)
        # self.downloader = YtDownloader()
        # self.downloader.track_download_started.connect(self.on_track_download_started)
        # self.downloader.track_download_progress.connect(self.on_track_download_progress)
        # self.downloader.track_download_finished.connect(self.on_track_download_finished)

        # Local songs
        self.local_songs_model = LocalSongsModel()
        self.local_songs_delegate = LocalSongsItemDelegate()
        self.local_songs_delegate.artist_clicked.connect(self.on_local_song_artist_clicked)
        self.local_songs_delegate.album_clicked.connect(self.on_local_song_album_clicked)
        self.ui.localSongs.row_clicked.connect(self.on_local_song_clicked)
        self.ui.localSongs.row_double_clicked.connect(self.on_local_song_double_clicked)
        self.ui.localSongs.setSpacing(6)
        self.ui.localSongs.setModel(self.local_songs_model)
        self.ui.localSongs.setItemDelegate(self.local_songs_delegate)

        self.local_artists_model = LocalArtistsModel()
        self.local_artists_delegate = LocalArtistsItemDelegate()
        self.ui.localArtists.row_clicked.connect(self.on_local_artist_clicked)
        self.ui.localArtists.setSpacing(6)
        self.ui.localArtists.setModel(self.local_artists_model)
        self.ui.localArtists.setItemDelegate(self.local_artists_delegate)

        self.local_albums_model = LocalAlbumsModel()
        self.local_albums_delegate = LocalAlbumsItemDelegate()
        self.local_albums_delegate.artist_clicked.connect(self.on_local_album_artist_clicked)
        # self.local_albums_delegate.album_clicked.connect(self.on_local_album_clicked)
        self.ui.localAlbums.row_clicked.connect(self.on_local_album_clicked)
        # self.ui.localAlbums.row_double_clicked.connect(self.on_local_song_double_clicked)
        self.ui.localAlbums.setSpacing(6)
        self.ui.localAlbums.setModel(self.local_albums_model)
        self.ui.localAlbums.setItemDelegate(self.local_albums_delegate)

        self.ui.localSongsButton.clicked.connect(self.on_local_songs_button_clicked)
        self.ui.localArtistsButton.clicked.connect(self.on_local_artists_button_clicked)
        self.ui.localAlbumsButton.clicked.connect(self.on_local_albums_button_clicked)
        self.on_local_songs_button_clicked()

        # Load local songs
        # TODO: preferences flag?
        localsongs.load_mp3s_background(
            preferences.directory(),
            mp3_loaded_callback=self.on_mp3_loaded,
            finished_callback=self.on_mp3s_loaded,
            load_images=False
        )

    def set_local_page(self):
        self.push_page(self.ui.localPage)

    def set_search_page(self):
        self.push_page(self.ui.searchPage)

    def set_downloads_page(self):
        self.push_page(self.ui.downloadsPage)

    def set_album_page(self):
        self.push_page(self.ui.albumPage)

    def set_artist_page(self):
        self.push_page(self.ui.artistPage)

    def current_page(self):
        return self.pages_stack[self.pages_stack_cursor] if 0 <= self.pages_stack_cursor <= len(self.pages_stack) - 1 else None

    def push_page(self, page):
        if self.current_page() == page:
            return

        self.pages_stack_cursor = self.pages_stack_cursor + 1
        self.pages_stack = self.pages_stack[:self.pages_stack_cursor]
        self.pages_stack.append(page)
        self.update_current_page()

    def prev_page(self):
        self.pages_stack_cursor = self.pages_stack_cursor - 1
        self.update_current_page()

    def next_page(self):
        self.pages_stack_cursor = self.pages_stack_cursor + 1
        self.update_current_page()

    def update_current_page(self):
        def page_to_string(p):
            if p == self.ui.localPage:
                return "local"
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

        if next_page == self.ui.localPage:
            self.select_page_button(self.ui.localPageButton)
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
        btn.setStyleSheet(f"padding: 6px; background-color: {'#565757' if self.dark_mode else '#b8b8b8'};")


    def open_release_group(self, release_group: ReleaseGroup):
        if not isinstance(release_group, ReleaseGroup):
            raise TypeError(f"Expected object of type 'ReleaseGroup', found {type(release_group)}")

        debug(f"open_release_group({release_group.id})")

        self.current_release_group_id = release_group.id

        # title
        self.ui.albumTitle.setText(release_group.title)

        # artist
        self.ui.albumArtist.setText(release_group.artists_string())

        # icon
        cover = release_group.preferred_front_cover()
        self.ui.albumCover.setPixmap(make_pixmap_from_data(cover, default=resources.COVER_PLACEHOLDER_PIXMAP))
        self.album_cover_data = cover
        self.set_album_cover(release_group.id)

        # download
        self.ui.albumDownloadAllButton.setEnabled(False)
        self.ui.albumDownloadAllButton.setText(f"Download missing songs")
        self.ui.albumDownloadStatus.setText("")

        # tracks
        self.album_tracks_model.release_id = None
        self.ui.albumTracks.invalidate()

        # year
        self.ui.albumYear.setText("")

        # song count
        self.ui.albumSongCount.setText("")

        # switch page
        self.set_album_page()

        # fetch the main release and its tracks
        repository.fetch_release_group_releases(release_group.id, self.on_release_group_releases_result, self.on_release_group_youtube_tracks_result)


    def open_mp3_release_group(self, mp3: Mp3):
        # already fetched: open directly
        if mp3.fetched_release_group and mp3.release_group_id:
            self.open_release_group(get_release_group(mp3.release_group_id))
            return

        # fetch it by name
        self.current_release_group_id = None

        # title
        self.ui.albumTitle.setText(mp3.album)

        # artist
        self.ui.albumArtist.setText(mp3.artist or "")

        # icon
        self.ui.albumCover.setPixmap(make_pixmap_from_data(mp3.image, default=resources.COVER_PLACEHOLDER_PIXMAP))
        self.album_cover_data = mp3.image
        self.ui.albumCoverNumber.setText("")

        # download
        self.ui.albumDownloadAllButton.setEnabled(False)
        self.ui.albumDownloadAllButton.setText(f"Download missing songs")
        self.ui.albumDownloadStatus.setText("")

        # tracks
        self.album_tracks_model.release_id = None
        self.ui.albumTracks.invalidate()

        # switch page
        self.set_album_page()

        # TODO: handle image blink

        def mp3_release_group_callback(mp3_, release_group):
            self.open_release_group(release_group)

        def mp3_release_group_image_callback(release_group_id, img):
            self.handle_album_cover_update(release_group_id)

        repository.fetch_mp3_release_group(mp3, mp3_release_group_callback, mp3_release_group_image_callback)

    def open_release_group_by_name(self, release_group_name: str, artist_name_hint: str=None):
        # fetch it by name
        self.current_release_group_id = None

        # title
        self.ui.albumTitle.setText(release_group_name)

        # artist
        self.ui.albumArtist.setText(artist_name_hint or "")

        # icon
        self.ui.albumCover.setPixmap(resources.COVER_PLACEHOLDER_PIXMAP)
        self.album_cover_data = None
        self.ui.albumCoverNumber.setText("")

        # download
        self.ui.albumDownloadAllButton.setEnabled(False)
        self.ui.albumDownloadAllButton.setText(f"Download missing songs")
        self.ui.albumDownloadStatus.setText("")

        # tracks
        self.album_tracks_model.release_id = None
        self.ui.albumTracks.invalidate()

        # switch page
        self.set_album_page()

        # TODO: handle image blink

        def release_group_callback(release_group_name_, release_group):
            self.open_release_group(release_group)

        def release_group_image_callback(release_group_id, img):
            self.handle_album_cover_update(release_group_id)

        repository.fetch_release_group_by_name(release_group_name, artist_name_hint, release_group_callback, release_group_image_callback)



    def open_artist(self, artist: Artist):
        if not isinstance(artist, Artist):
            raise TypeError(f"Expected object of type 'Artist', found {type(artist)}")
        debug(f"open_artist({artist.id})")

        self.current_artist_id = artist.id

        # title
        self.ui.artistName.setText(artist.name)

        # icon
        cover = artist.image
        self.ui.artistCover.setPixmap(make_pixmap_from_data(cover, default=resources.PERSON_PLACEHOLDER_PIXMAP))
        self.artist_cover_data = cover

        # albums
        self.artist_albums_model.artist_id = artist.id
        self.ui.artistAlbums.invalidate()

        # switch page
        self.set_artist_page()

        # fetch the artist details (e.g. artist release groups)
        repository.fetch_artist(artist.id, self.on_artist_result, self.on_artist_image_result)


    def open_mp3_artist(self, mp3: Mp3):
        # already fetched: open directly
        if mp3.fetched_artist and mp3.artist_id:
            self.open_artist(get_artist(mp3.artist_id))
            return

        self.current_artist_id = None

        # title
        self.ui.artistName.setText(mp3.artist)

        # icon
        # self.ui.artistCover.setPixmap(make_pixmap_from_data(mp3.image, default=resources.COVER_PLACEHOLDER_PIXMAP))
        self.ui.artistCover.setPixmap(resources.COVER_PLACEHOLDER_PIXMAP)
        self.artist_cover_data = None

        # albums
        self.artist_albums_model.artist_id = None
        self.ui.artistAlbums.invalidate()

        # switch page
        self.set_artist_page()

        def mp3_artist_callback(mp3_, artist):
            self.open_artist(artist)

        def mp3_artist_image_callback(artist_id, img):
            self.on_artist_image_result(artist_id, img)

        repository.fetch_mp3_artist(mp3, mp3_artist_callback, mp3_artist_image_callback)


    def open_artist_by_name(self, artist_name: str):
        # already fetched: open directly

        self.current_artist_id = None

        # title
        self.ui.artistName.setText(artist_name)

        # icon
        self.ui.artistCover.setPixmap(resources.COVER_PLACEHOLDER_PIXMAP)
        self.artist_cover_data = None

        # albums
        self.artist_albums_model.artist_id = None
        self.ui.artistAlbums.invalidate()

        # switch page
        self.set_artist_page()

        def artist_callback(artist_name_, artist):
            self.open_artist(artist)

        def artist_image_callback(artist_id, img):
            self.on_artist_image_result(artist_id, img)

        repository.fetch_artist_by_name(artist_name, artist_callback, artist_image_callback)


    def on_action_preferences(self):
        debug("on_action_preferences")
        preferences_window = PreferencesWindow()
        preferences_window.exec()

    def on_local_page_button_clicked(self, ev: QMouseEvent):
        self.set_local_page()

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

        repository.search_artists(
            query,
            artists_callback=self.on_search_artists_result,
            artist_image_callback=self.on_artist_image_result,
        )
        repository.search_release_groups(
            query,
            release_groups_callback=self.on_search_release_groups_result,
            release_group_image_callback=self.on_release_group_image_result,
        )
        repository.search_tracks(
            query,
            tracks_callback=self.on_search_tracks_result,
            track_image_callback=self.on_track_image_result,
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

        rg = get_release_group(release_group_id)
        if rg and self.current_release_group_id == rg.id:
            main_release_id = rg.main_release_id
            main_release = get_release(main_release_id)
            if main_release:
                self.album_tracks_model.release_id = main_release_id
                self.ui.albumTracks.invalidate()
                self.ui.albumYear.setText(rg.year())
                self.ui.albumSongCount.setText(f"{main_release.track_count()} songs - {millis_to_human_string(main_release.length())}")

                self.set_album_cover(release_group_id)
                self.update_album_download_widgets()

        self.ui.artistAlbums.update_row(release_group_id)

        # repository.search_release_youtube_tracks(main_release_id, self.on_release_youtube_tracks_result)


    def on_search_tracks_result(self, query, tracks: List[Track]):
        debug(f"on_search_tracks_result(query={query})")

        pending_changes = False

        if query != self.last_search_query:
            debug("Clearing search results")
            self.last_search_query = query
            self.search_results_model.results.clear()
            pending_changes = True

        for track in tracks:
            self.search_results_model.results.append(track.id)
            pending_changes = True

        if pending_changes:
            self.ui.searchResults.invalidate()

    def on_release_group_image_result(self, release_group_id, image):
        debug(f"on_release_group_image_result(release_group_id={release_group_id})")

        self.handle_album_cover_update(release_group_id)

    def on_track_image_result(self, track_id, image):
        debug(f"on_track_image_result(track_id={track_id})")

        self.handle_album_cover_update(get_track(track_id).release().release_group_id)

        # TODO: not here/better
        # search page
        debug("Updating search result with track image")
        self.ui.searchResults.update_row(track_id)

    def on_artist_result(self, artist_id, artist: Artist):
        debug(f"on_artist_result(artist_id={artist_id})")

        if self.current_artist_id == artist_id:
            self.ui.artistAlbums.invalidate()

        for rg_id in artist.release_group_ids:
            repository.fetch_release_group_releases(rg_id,
                                                    self.on_release_group_releases_result,
                                                    self.on_release_group_youtube_tracks_result,
                                                    priority=workers.Worker.PRIORITY_IDLE)
            repository.fetch_release_group_cover(rg_id, self.on_release_group_image_result)

    def on_artist_image_result(self, artist_id, image):
        debug(f"on_artist_image_result(artist_id={artist_id})")

        # search page
        self.ui.searchResults.update_row(artist_id)

        # artist page
        if self.current_artist_id == artist_id:
            image = get_artist(artist_id).image
            self.ui.artistCover.setPixmap(make_pixmap_from_data(
                image, default=resources.PERSON_PLACEHOLDER_PIXMAP)
            )
            self.artist_cover_data = image

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

    def on_search_result_subtitle_first_clicked(self, row: int):
        debug(f"on_search_result_subtitle_first_clicked({row})")

        result_id = self.search_results_model.results[row]
        result = get_entity(result_id)

        if isinstance(result, ReleaseGroup):
            # TODO: what if there is more than an arist?
            # should probably add different labels separated by commasS
            self.open_artist(result.artists()[0])
        elif isinstance(result, Artist):
            print("WARN: wtf?")
        elif isinstance(result, Track):
            self.open_artist(result.release().release_group().artists()[0])
        else:
            print("WARN: not supported yet")

    def on_search_result_subtitle_second_clicked(self, row: int):
        debug(f"on_search_result_subtitle_second_clicked({row})")

        result_id = self.search_results_model.results[row]
        result = get_entity(result_id)

        if isinstance(result, ReleaseGroup):
            print("WARN: wtf?")
        elif isinstance(result, Artist):
            print("WARN: wtf?")
        elif isinstance(result, Track):
            self.open_release_group(result.release().release_group())
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
        self.album_change_cover_empty_image_callback = self.on_album_cover_prev_button_clicked
        self.handle_album_cover_change_request(direction="prev")


    def on_album_cover_next_button_clicked(self):
        debug("on_album_cover_next_button_clicked")
        self.album_change_cover_empty_image_callback = self.on_album_cover_next_button_clicked
        self.handle_album_cover_change_request(direction="next")

    def handle_album_cover_change_request(self, direction):
        if direction == "next":
            delta = 1
        elif direction == "prev":
            delta = -1
        else:
            raise ValueError(f"Unexpected direction: {direction}")

        self.ui.albumCover.setPixmap(resources.COVER_PLACEHOLDER_PIXMAP)
        self.album_cover_data = None
        self.ui.albumCoverNumber.setText("")

        release_group = get_release_group(self.current_release_group_id)

        debug(f"Preferred cover index was: {release_group.preferred_front_cover_index}")
        release_group.move_preferred_front_cover_index(delta)
        debug(f"Preferred cover index is: {release_group.preferred_front_cover_index}")

        self.ui.albumCoverNumber.setText(f"{release_group.preferred_front_cover_index + 1}/{release_group.front_cover_count()}")

        if release_group.preferred_front_cover_index == repository.RELEASE_GROUP_IMAGES_RELEASE_GROUP_COVER_INDEX:
            # release group
            repository.fetch_release_group_cover(release_group.id, self.on_change_album_cover_release_group_image_result)
        else:
            # release
            release = get_release(release_group.release_ids[release_group.preferred_front_cover_index - repository.RELEASE_GROUP_IMAGES_RELEASES_FIRST_INDEX])
            repository.fetch_release_cover(release.id, self.on_change_album_cover_release_image_result)


    def on_change_album_cover_release_group_image_result(self, release_group_id, image):
        debug(f"on_change_album_cover_release_group_image_result(release_group_id={release_group_id})")

        if not image:
            self.album_change_cover_empty_image_callback()
            return

        release_group = get_release_group(release_group_id)
        release_group.set_preferred_front_cover_release_group()

        self.handle_album_cover_update(release_group_id)

    def on_change_album_cover_release_image_result(self, release_id, image):
        debug(f"on_album_cover_change_image_result(release_id={release_id})")

        if not image:
            self.album_change_cover_empty_image_callback()
            return

        release_group = get_release(release_id).release_group()
        release_group.set_preferred_front_cover_release(release_id)

        self.handle_album_cover_update(release_group.id)

    def handle_album_cover_update(self, release_group_id):

        release_group = get_release_group(release_group_id)

        # search page
        self.ui.searchResults.update_row(release_group.id)

        # album page
        if self.current_release_group_id == release_group.id:
            self.set_album_cover(release_group.id)

        # artist page
        self.ui.artistAlbums.update_row(release_group.id)

        # tracks
        self.ui.albumTracks.invalidate()

    def set_album_cover(self, release_group_id):
        release_group = get_release_group(release_group_id)
        debug(f"Updating album cover")

        cover = release_group.preferred_front_cover()
        self.ui.albumCover.setPixmap(make_pixmap_from_data(
            cover, default=resources.COVER_PLACEHOLDER_PIXMAP)
        )
        self.album_cover_data = cover

        self.ui.albumCoverNumber.setText(f"{release_group.preferred_front_cover_index + 1}/{release_group.front_cover_count()}")

        self.update_album_cover_state()

    def update_album_cover_state(self):
        release_group = get_release_group(self.current_release_group_id)
        if release_group:
            main = release_group.main_release()
            locally_available_track_count = main.locally_available_track_count() if main else 0
            if locally_available_track_count == 0:
                self.ui.albumCover.setStyleSheet(resources.LOCALLY_UNAVAILABLE_STYLESHEET)
            elif locally_available_track_count == main.track_count():
                self.ui.albumCover.setStyleSheet(resources.LOCALLY_AVAILABLE_STYLESHEET)
            else:
                self.ui.albumCover.setStyleSheet(resources.LOCALLY_PARTIALLY_AVAILABLE_STYLESHEET)

    def on_album_cover_double_clicked(self, ev: QMouseEvent):
        debug("on_album_cover_double_clicked")
        image_preview_window = ImagePreviewWindow()
        image_preview_window.set_image(self.album_cover_data)
        image_preview_window.exec()

    def on_artist_image_double_clicked(self, ev: QMouseEvent):
        debug("on_artist_image_double_clicked")
        image_preview_window = ImagePreviewWindow()
        image_preview_window.set_image(self.artist_cover_data)
        image_preview_window.exec()

    def on_release_group_youtube_tracks_result(self, release_group_id: str, yttracks: List[YtTrack]):
        debug("on_release_group_youtube_tracks_result")

        # fetch missing ones
        release = get_release_group(release_group_id).main_release()

        missing = 0
        for t in release.tracks():
            if not t.fetched_youtube_track:
                missing += 1
                repository.search_track_youtube_track(t.id, self.on_track_youtube_track_result)

        if missing:
            debug(f"After release tracks fetching there was still {missing} "
                  f"missing tracks missing youtube video, searching now")

        self.handle_youtube_tracks_update(release.id)


    def on_track_youtube_track_result(self, track_id: str, yttrack: YtTrack):
        track = get_track(track_id)
        # self.ui.albumTracks.update_row(track_id) # would be more precise
        self.handle_youtube_tracks_update(track.release_id)


    def on_track_download_button_clicked(self, row: int):
        debug("on_track_download_button_clicked")
        track_id = self.album_tracks_model.entry(row)
        self.do_download_youtube_track(track_id)

    def on_track_open_video_button_clicked(self, row: int):
        debug("on_track_open_video_button_clicked")
        track_id = self.album_tracks_model.entry(row)
        track = get_track(track_id)
        yttrack = get_youtube_track(track.youtube_track_id)

        open_url(ytcommons.youtube_video_id_to_youtube_music_url(yttrack.video_id))

    def handle_youtube_tracks_update(self, release_id):
        release = get_release(release_id)

        if self.current_release_group_id == release.release_group_id:
            self.ui.albumTracks.invalidate()

            self.update_album_download_widgets()

    def update_album_download_widgets(self):
        rg = get_release_group(self.current_release_group_id)
        if not rg:
            debug("update_album_download_widgets: no release group")
            return

        release = get_release_group(self.current_release_group_id).main_release()
        if not release:
            debug("update_album_download_widgets: no main release for release group")
            return

        tracks = release.tracks()
        # Download missing tracks button
        missing_downloadable = 0
        verified = 0
        for track in tracks:
            if track.fetched_youtube_track and track.youtube_track_id:
                if track.youtube_track_is_official:
                    verified += 1
                if not track.is_locally_available() and not track.downloading:
                    missing_downloadable += 1

        self.ui.albumDownloadAllButton.setEnabled(missing_downloadable > 0)
        if missing_downloadable > 0:
            self.ui.albumDownloadAllButton.setText(f"Download missing songs ({missing_downloadable})")
        else:
            self.ui.albumDownloadAllButton.setText(f"Download missing songs")

        # Download missing tracks status
        self.ui.albumDownloadStatus.setText(f"Verified songs: {verified}/{release.track_count()}")
        self.ui.albumDownloadStatus.setToolTip("\n".join([f'{t.title} [{"verified" if t.youtube_track_is_official else "not verified"}]' for t in tracks]))


    def on_youtube_track_download_queued(self, down: dict):
        debug(f"on_youtube_track_download_queued(video_id={down['video_id']})")
        if down["user_data"]["type"] == "manual":
            self.ui.manualDownloadButton.setEnabled(True)

        self.ui.queuedDownloads.invalidate()
        self.update_downloads_count()

        self.update_album_download_widgets()
        if down["user_data"]["type"] == "official":
            track_id = down["user_data"]["id"]
            self.ui.albumTracks.update_row(track_id)

    def on_youtube_track_download_started(self, down: dict):
        debug(f"on_youtube_track_download_started(video_id={down['video_id']})")
        self.ui.queuedDownloads.invalidate()
        self.update_downloads_count()
        self.update_album_download_widgets()
        if down["user_data"]["type"] == "official":
            track_id = down["user_data"]["id"]
            self.ui.albumTracks.update_row(track_id)

    def on_youtube_track_download_progress(self, down: dict, progress: float):
        debug(f"on_youtube_track_download_progress(video_id={down['video_id']}, progress={progress})")
        video_id = down["video_id"]
        self.ui.queuedDownloads.update_row(video_id)

        if down["user_data"]["type"] == "official":
            track_id = down["user_data"]["id"]
            self.ui.albumTracks.update_row(track_id)

    def on_youtube_track_download_finished(self, down: dict):
        debug(f"on_youtube_track_download_finished(video_id={down['video_id']})")
        self.ui.queuedDownloads.invalidate()
        self.ui.finishedDownloads.invalidate()
        self.update_downloads_count()
        self.update_album_download_widgets()
        self.update_album_cover_state()

        debug("Reloading mp3s model")
        self.update_local_song_count()
        self.local_songs_model.beginResetModel()
        self.local_songs_model.endResetModel()

        if down["user_data"]["type"] == "official":
            track_id = down["user_data"]["id"]
            self.ui.albumTracks.update_row(track_id)

            t = get_track(track_id)
            if t:
                self.ui.artistAlbums.update_row(t.release().release_group_id)  # album state in artist page


    def on_youtube_track_download_canceled(self, down: dict):
        debug(f"on_youtube_track_download_canceled(video_id={down['video_id']})")
        self.ui.queuedDownloads.invalidate()
        self.update_downloads_count()
        self.update_album_download_widgets()
        if down["user_data"]["type"] == "official":
            track_id = down["user_data"]["id"]
            self.ui.albumTracks.update_row(track_id)

    def on_youtube_track_download_error(self, down: dict, error_msg: str):
        debug(f"on_youtube_track_download_error(video_id={down['video_id']}): {error_msg}")

        if down["user_data"]["type"] == "manual":
            self.ui.manualDownloadButton.setEnabled(True)

        self.ui.queuedDownloads.invalidate()
        self.ui.finishedDownloads.invalidate()
        self.update_downloads_count()
        self.update_album_download_widgets()
        if down["user_data"]["type"] == "official":
            track_id = down["user_data"]["id"]
            self.ui.albumTracks.update_row(track_id)

    def update_downloads_count(self):
        queued_count = ytdownloader.download_count()
        finished_count = ytdownloader.finished_download_count()
        self.ui.downloadsPageButton.setText(f"Downloads ({queued_count})" if queued_count else "Downloads")
        self.ui.downloadsTabs.setTabText(DOWNLOADS_TABS_QUEUED_INDEX, f"Queue ({queued_count})" if queued_count else "Queue")
        self.ui.downloadsTabs.setTabText(DOWNLOADS_TABS_COMPLETED_INDEX, f"Completed ({finished_count})" if finished_count else "Completed")

    def on_download_missing_album_tracks_clicked(self):
        debug("on_download_all_album_tracks_clicked")
        rg = get_release_group(self.current_release_group_id)
        for track in rg.main_release().tracks():
            if not track.is_locally_available() and not track.downloading:
                self.do_download_youtube_track(track.id)

    def do_download_youtube_track(self, track_id):
        repository.download_youtube_track(track_id,
                                          queued_callback=self.on_youtube_track_download_queued,
                                          started_callback=self.on_youtube_track_download_started,
                                          progress_callback=self.on_youtube_track_download_progress,
                                          finished_callback=self.on_youtube_track_download_finished,
                                          canceled_callback=self.on_youtube_track_download_canceled,
                                          error_callback=self.on_youtube_track_download_error)

    def on_download_cancel_button_clicked(self, row: int):
        debug("on_download_cancel_button_clicked")
        down = self.downloads_model.entry(row)
        repository.cancel_youtube_track_download(down["video_id"])

    def on_download_artist_clicked(self, row: int):
        debug("on_download_artist_clicked")
        down = self.downloads_model.entry(row)
        if down["user_data"]["type"] == "official":
            track = get_track(down["user_data"]["id"])
            if track:
                # TODO: more than an artist
                artist = track.release().release_group().artists()[0]
                self.open_artist(artist)
        elif down["user_data"]["type"] == "manual":
            self.open_artist_by_name(artist_name=down["artist"])

    def on_download_album_clicked(self, row: int):
        debug("on_download_album_clicked")
        down = self.downloads_model.entry(row)
        if down["user_data"]["type"] == "official":
            track = get_track(down["user_data"]["id"])
            if track:
                rg = track.release().release_group()
                self.open_release_group(rg)
        elif down["user_data"]["type"] == "manual":
            self.open_release_group_by_name(release_group_name=down["album"], artist_name_hint=down["artist"])

    def on_finished_download_artist_clicked(self, row: int):
        debug("on_download_artist_clicked")
        down = self.finished_downloads_model.entry(row)
        if down["user_data"]["type"] == "official":
            track = get_track(down["user_data"]["id"])
            # TODO: more than an artist
            artist = track.release().release_group().artists()[0]
            self.open_artist(artist)
        elif down["user_data"]["type"] == "manual":
            self.open_artist_by_name(artist_name=down["artist"])


    def on_finished_download_album_clicked(self, row: int):
        debug("on_download_album_clicked")
        down = self.finished_downloads_model.entry(row)
        if down["user_data"]["type"] == "official":
            track = get_track(down["user_data"]["id"])
            if track:
                rg = track.release().release_group()
                self.open_release_group(rg)
        elif down["user_data"]["type"] == "manual":
            self.open_release_group_by_name(release_group_name=down["album"], artist_name_hint=down["artist"])


    def on_mp3_loaded(self, mp3: Mp3):
        self.update_local_song_count()

    def on_mp3s_loaded(self, with_images):
        # self.ui.localSongs.invalidate()
        debug("Reloading mp3s model")
        self.reload_local_songs_artists_albums()
        if not with_images:
            debug("Loading images now")
            localsongs.load_mp3s_images_background(
                mp3_image_loaded_callback=self.on_mp3_image_loaded,
                finished_callback=self.on_mp3s_images_loaded)


    def on_mp3_image_loaded(self, mp3: Mp3):
        pass

    def on_mp3s_images_loaded(self):
        debug("Reloading mp3s model")
        # self.ui.localSongs.invalidate()
        self.reload_local_songs_artists_albums()

    def on_action_reload(self):
        # Reload mp3s
        localsongs.clear_mp3s()

        self.reload_local_songs_artists_albums()

        self.update_local_song_count()
        localsongs.load_mp3s_background(preferences.directory(),
                                        mp3_loaded_callback=self.on_mp3_loaded,
                                        finished_callback=self.on_mp3s_loaded,
                                        load_images=False)

    def reload_local_songs_artists_albums(self):
        self.local_songs_model.beginResetModel()
        self.local_songs_model.endResetModel()

        self.local_artists_model.beginResetModel()
        self.local_artists_model.reload()
        self.local_artists_model.endResetModel()

        self.local_albums_model.beginResetModel()
        self.local_albums_model.reload()
        self.local_albums_model.endResetModel()

    def update_local_song_count(self):
        self.ui.localSongCount.setText(f"{len(localsongs.mp3s)} songs")

    def on_manual_download_button_clicked(self):
        # TODO: implement musicbrainz fetching based on yt metadata?
        # actually this is bugged since the down its not shown


        debug("on_manual_download_button_clicked")
        url = self.ui.manualDownloadURL.text()
        self.ui.manualDownloadURL.setText("")
        self.ui.manualDownloadButton.setEnabled(False)

        video_id = ytcommons.youtube_url_to_video_id(url)
        playlist_id = ytcommons.youtube_url_to_playlist_id(url)

        if not (video_id or playlist_id):
            print("WARN: invalid youtube url")
            QMessageBox.warning(self, "Invalid URL",
                                "Invalid YouTube URL",
                                QMessageBox.Ok)
            return

        if video_id:
            debug(f"Detected youtube video: {video_id}")
            repository.download_youtube_track_manual(
                video_id=video_id,
                queued_callback=self.on_youtube_track_download_queued,
                started_callback=self.on_youtube_track_download_started,
                progress_callback=self.on_youtube_track_download_progress,
                finished_callback=self.on_youtube_track_download_finished,
                canceled_callback=self.on_youtube_track_download_canceled,
                error_callback=self.on_youtube_track_download_error,
            )
        elif playlist_id:
            debug(f"Detected youtube playlist: {playlist_id}")
            repository.download_youtube_playlist_manual(
                playlist_id=playlist_id,
                queued_callback=self.on_youtube_track_download_queued,
                started_callback=self.on_youtube_track_download_started,
                progress_callback=self.on_youtube_track_download_progress,
                finished_callback=self.on_youtube_track_download_finished,
                canceled_callback=self.on_youtube_track_download_canceled,
                error_callback=self.on_youtube_track_download_error,
            )


    def on_local_song_artist_clicked(self, row: int):
        mp3 = localsongs.mp3s[row]
        debug(f"on_local_song_artist_clicked: {mp3}")
        self.open_mp3_artist(mp3)

    def on_local_song_album_clicked(self, row: int):
        mp3 = localsongs.mp3s[row]
        debug(f"on_local_song_album_clicked: {mp3}")
        self.open_mp3_release_group(mp3)

    def on_local_song_clicked(self, row: int):
        mp3 = localsongs.mp3s[row]
        debug(f"on_local_song_clicked: {mp3}")

    def on_local_song_double_clicked(self, row: int):
        mp3 = localsongs.mp3s[row]
        debug(f"on_local_song_double_clicked: {mp3}")
        if mp3.path:
            debug(f"Mp3 path: {mp3.path}")
            open_folder(mp3.path.parent)

    def on_finished_download_double_clicked(self, row: int):
        debug("on_finished_download_double_clicked")
        down = self.finished_downloads_model.entry(row)
        if down:
            debug(f"Associated download: {down}")
            folder = down.get("file")
            if folder:
                debug(f"Opening folder of {folder}")
                open_folder(Path(folder).parent)

    def on_local_songs_button_clicked(self):
        debug("on_local_songs_button_clicked")
        self.ui.localPages.setCurrentWidget(self.ui.localSongsPage)
        self.ui.localSongsButton.setStyleSheet(resources.PILL_HIGHLIGHTED_STYLESHEET)
        self.ui.localArtistsButton.setStyleSheet(resources.PILL_UNHIGHLIGHTED_STYLESHEET)
        self.ui.localAlbumsButton.setStyleSheet(resources.PILL_UNHIGHLIGHTED_STYLESHEET)

    def on_local_artists_button_clicked(self):
        debug("on_local_artists_button_clicked")
        self.ui.localPages.setCurrentWidget(self.ui.localArtistsPage)
        self.ui.localSongsButton.setStyleSheet(resources.PILL_UNHIGHLIGHTED_STYLESHEET)
        self.ui.localArtistsButton.setStyleSheet(resources.PILL_HIGHLIGHTED_STYLESHEET)
        self.ui.localAlbumsButton.setStyleSheet(resources.PILL_UNHIGHLIGHTED_STYLESHEET)

    def on_local_albums_button_clicked(self):
        debug("on_local_albums_button_clicked")
        self.ui.localPages.setCurrentWidget(self.ui.localAlbumsPage)
        self.ui.localSongsButton.setStyleSheet(resources.PILL_UNHIGHLIGHTED_STYLESHEET)
        self.ui.localArtistsButton.setStyleSheet(resources.PILL_UNHIGHLIGHTED_STYLESHEET)
        self.ui.localAlbumsButton.setStyleSheet(resources.PILL_HIGHLIGHTED_STYLESHEET)

    def on_local_artist_clicked(self, row: int):
        debug("on_local_artist_clicked")
        mp3_group_leader = self.local_artists_model.entry(row)
        self.open_mp3_artist(mp3_group_leader)

        # self.on_local_artist_clicked()

    def on_local_album_clicked(self, row: int):
        debug("on_local_album_clicked")
        mp3_group_leader = self.local_albums_model.entry(row)
        self.open_mp3_release_group(mp3_group_leader)

    def on_local_album_artist_clicked(self, row: int):
        debug("on_local_album_artist_clicked")
        mp3_group_leader = self.local_albums_model.entry(row)
        self.open_mp3_artist(mp3_group_leader)