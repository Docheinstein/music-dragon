import random
from pathlib import Path
from typing import List, Union, Optional

from PyQt5.QtCore import QTimer, QSortFilterProxyModel, QRegularExpression
from PyQt5.QtGui import QFont, QMouseEvent, QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QLabel, QMessageBox

from music_dragon import localsongs, repository, workers, ytcommons, ytdownloader, preferences, audioplayer, cache, favourites, \
    UNKNOWN_ARTIST, UNKNOWN_ALBUM
from music_dragon.localsongs import Mp3
from music_dragon.log import debug
from music_dragon.repository import Artist, ReleaseGroup, Release, Track, get_artist, \
    get_release_group, get_entity, get_track, get_release, get_youtube_track
from music_dragon.ui import resources
from music_dragon.ui.albumtrackswidget import AlbumTracksModel
from music_dragon.ui.artistalbumswidget import ArtistAlbumsModel
from music_dragon.ui.downloadswidget import DownloadsModel, FinishedDownloadsModel
from music_dragon.ui.editlinkwindow import EditLinkWindow
from music_dragon.ui.imagepreviewwindow import ImagePreviewWindow
from music_dragon.ui.localalbumsview import LocalAlbumsModel, LocalAlbumsItemDelegate, LocalAlbumsProxyModel
from music_dragon.ui.localalbumtrackswidget import LocalAlbumTracksModel
from music_dragon.ui.localartistalbumswidget import LocalArtistAlbumsModel
from music_dragon.ui.localartistsview import LocalArtistsModel, LocalArtistsItemDelegate, LocalArtistsProxyModel
from music_dragon.ui.localsongsview import LocalSongsModel, LocalSongsItemDelegate, LocalSongsProxyModel
from music_dragon.ui.preferenceswindow import PreferencesWindow
from music_dragon.ui.searchresultswidget import SearchResultsModel
from music_dragon.ui.ui_mainwindow import Ui_MainWindow
from music_dragon.utils import make_pixmap_from_data, open_url, open_folder, is_dark_mode, millis_to_long_string, \
    millis_to_short_string, rangify
from music_dragon.ytcommons import youtube_playlist_id_to_youtube_url, youtube_url_to_playlist_id
from music_dragon.ytmusic import YtTrack

SEARCH_DEBOUNCE_MS = 800

DOWNLOADS_TABS_QUEUED_INDEX = 0
DOWNLOADS_TABS_COMPLETED_INDEX = 1


class PlayingInfo:
    def __init__(self):
        self.index = 0
        self.queue: List[Union[Track, Mp3]] = []

    def in_play(self) -> Optional[Union[Track, Mp3]]:
        if 0 <= self.index < len(self.queue):
            return self.queue[self.index]
        return None

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
        self.album_change_cover_initial_index = None

        self.ui.albumTracks.link_button_clicked.connect(self.on_track_link_button_clicked)
        self.ui.albumTracks.download_button_clicked.connect(self.on_track_download_button_clicked)
        self.ui.albumTracks.open_video_button_clicked.connect(self.on_track_open_video_button_clicked)
        self.ui.albumTracks.row_double_clicked.connect(self.on_track_double_clicked)
        self.ui.albumDownloadAllButton.clicked.connect(self.on_download_missing_album_tracks_clicked)
        self.ui.albumDownloadAllVerifiedCheck.stateChanged.connect(self.on_download_missing_album_tracks_verified_check_changed)
        self.ui.albumOpenButton.clicked.connect(self.on_open_album_button_clicked)

        self.ui.albumLinkButton.clicked.connect(self.on_album_link_button_clicked)
        self.ui.albumLinkOkButton.clicked.connect(self.on_album_link_ok_button_clicked)
        self.ui.albumLinkCancelButton.clicked.connect(self.on_album_link_cancel_button_clicked)

        self.ui.albumLinkButton.setVisible(True)
        self.ui.albumLinkButton.setToolTip("Edit YouTube URL")
        sz = self.ui.albumLinkContainer.sizePolicy()
        sz.setRetainSizeWhenHidden(True)
        self.ui.albumLinkContainer.setSizePolicy(sz)
        self.ui.albumLinkContainer.setVisible(False)

        self.ui.showYouTubeTitlesCheck.stateChanged.connect(self.on_show_album_tracks_youtube_titles_check_changed)

        self.ui.albumOpenLocalButton.clicked.connect(self.on_album_open_local_button_clicked)

        # Artist
        self.current_artist_id = None
        self.artist_albums_model = ArtistAlbumsModel()
        self.ui.artistAlbums.set_model(self.artist_albums_model)
        self.ui.artistAlbums.row_clicked.connect(self.on_artist_album_clicked)
        self.ui.artistCover.double_clicked.connect(self.on_artist_image_double_clicked)
        self.ui.artistCover.set_clickable(False)
        self.ui.artistCover.set_double_clickable(True)
        self.artist_cover_data = None

        self.ui.artistOpenLocalButton.clicked.connect(self.on_artist_open_local_button_clicked)

        # Local Album
        self.current_local_album_mp3_group_leader = None
        self.local_album_tracks_model = LocalAlbumTracksModel()
        self.ui.localAlbumTracks.set_model(self.local_album_tracks_model)
        self.ui.localAlbumTracks.row_clicked.connect(self.on_local_album_track_clicked)

        self.ui.localAlbumArtist.set_underline_on_hover(True)
        self.ui.localAlbumArtist.clicked.connect(self.on_local_album_artist_clicked_2)

        self.ui.localAlbumCover.double_clicked.connect(self.on_local_album_cover_double_clicked)
        self.ui.localAlbumCover.set_clickable(False)
        self.ui.localAlbumCover.set_double_clickable(True)
        self.album_cover_data = None

        self.ui.localAlbumTracks.row_double_clicked.connect(self.on_local_track_double_clicked)
        self.ui.localAlbumOpenRemoteButton.clicked.connect(self.on_local_album_open_remote_button_clicked)
        self.ui.localAlbumRandomPlayButton.clicked.connect(self.on_local_album_random_play_button_clicked)

        self.ui.localAlbumFavouriteButton.clicked.connect(self.on_local_album_favourite_button_clicked)

        # Local Artist
        self.current_local_artist_mp3_group_leader = None

        self.local_artist_albums_model = LocalArtistAlbumsModel()
        self.ui.localArtistAlbums.set_model(self.local_artist_albums_model)
        self.ui.localArtistAlbums.row_clicked.connect(self.on_local_artist_album_clicked)
        self.ui.localArtistAlbums.favourite_button_clicked.connect(self.on_local_artist_favourite_album_button_clicked)

        self.ui.localArtistCover.double_clicked.connect(self.on_local_artist_image_double_clicked)

        self.ui.localArtistCover.set_clickable(False)
        self.ui.localArtistCover.set_double_clickable(True)

        self.ui.localArtistOpenRemoteButton.clicked.connect(self.on_local_artist_open_remote_button_clicked)
        self.ui.localArtistRandomPlayButton.clicked.connect(self.on_local_artist_random_play_button_clicked)

        self.ui.localArtistFavouriteButton.clicked.connect(self.on_local_artist_favourite_button_clicked)

        # Menu
        self.ui.actionPreferences.triggered.connect(self.on_action_preferences)
        self.ui.actionRefresh.triggered.connect(self.on_action_refresh)
        self.ui.actionReload.triggered.connect(self.on_action_reload)

        # Queued downloads
        self.downloads_model = DownloadsModel()
        self.ui.queuedDownloads.set_model(self.downloads_model)
        self.ui.queuedDownloads.cancel_button_clicked.connect(self.on_download_cancel_button_clicked)
        self.ui.queuedDownloads.artist_clicked.connect(self.on_download_artist_clicked)
        self.ui.queuedDownloads.album_clicked.connect(self.on_download_album_clicked)
        self.ui.autoDownloadQueuedCheck.stateChanged.connect(self.on_auto_download_queued_check_changed)

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
        self.local_songs_proxy_model = LocalSongsProxyModel()
        self.local_songs_proxy_model.setSourceModel(self.local_songs_model)
        self.local_songs_proxy_model.setFilterCaseSensitivity(0)
        self.local_songs_delegate = LocalSongsItemDelegate(self.local_songs_proxy_model)
        self.local_songs_delegate.artist_clicked.connect(self.on_local_song_artist_clicked)
        self.local_songs_delegate.album_clicked.connect(self.on_local_song_album_clicked)
        self.ui.localSongs.row_clicked.connect(self.on_local_song_clicked)
        self.ui.localSongs.row_double_clicked.connect(self.on_local_song_double_clicked)
        self.ui.localSongs.setSpacing(6)
        self.ui.localSongs.setModel(self.local_songs_proxy_model)
        self.ui.localSongs.setItemDelegate(self.local_songs_delegate)
        self.ui.localSongsFilter.textChanged.connect(self.on_local_songs_filter_changed)

        self.local_artists_model = LocalArtistsModel()
        self.local_artists_proxy_model = LocalArtistsProxyModel()
        self.local_artists_proxy_model.setSourceModel(self.local_artists_model)
        self.local_artists_proxy_model.setFilterCaseSensitivity(0)
        self.local_artists_delegate = LocalArtistsItemDelegate(self.local_artists_proxy_model)
        self.local_artists_delegate.favourite_clicked.connect(self.on_local_artists_favourite_clicked)
        self.ui.localArtists.row_clicked.connect(self.on_local_artist_clicked)
        self.ui.localArtists.setSpacing(6)
        self.ui.localArtists.setModel(self.local_artists_proxy_model)
        self.ui.localArtists.setItemDelegate(self.local_artists_delegate)
        self.ui.localArtistsFilter.textChanged.connect(self.on_local_artists_filter_changed)

        self.local_albums_model = LocalAlbumsModel()
        self.local_albums_proxy_model = LocalAlbumsProxyModel()
        self.local_albums_proxy_model.setSourceModel(self.local_albums_model)
        self.local_albums_proxy_model.setFilterCaseSensitivity(0)
        self.local_albums_delegate = LocalAlbumsItemDelegate(self.local_albums_proxy_model)
        self.local_albums_delegate.artist_clicked.connect(self.on_local_album_artist_clicked)
        self.local_albums_delegate.favourite_clicked.connect(self.on_local_albums_favourite_clicked)
        # self.local_albums_delegate.album_clicked.connect(self.on_local_album_clicked)
        self.ui.localAlbums.row_clicked.connect(self.on_local_album_clicked)
        # self.ui.localAlbums.row_double_clicked.connect(self.on_local_song_double_clicked)
        self.ui.localAlbums.setSpacing(6)
        self.ui.localAlbums.setModel(self.local_albums_proxy_model)
        self.ui.localAlbums.setItemDelegate(self.local_albums_delegate)
        self.ui.localAlbumsFilter.textChanged.connect(self.on_local_albums_filter_changed)

        self.ui.localSongsButton.clicked.connect(self.on_local_songs_button_clicked)
        self.ui.localArtistsButton.clicked.connect(self.on_local_artists_button_clicked)
        self.ui.localAlbumsButton.clicked.connect(self.on_local_albums_button_clicked)
        self.on_local_songs_button_clicked()

        self.ui.localSongsRandomPlayButton.clicked.connect(self.on_local_songs_random_play_button_clicked)


        # Load local songs
        # TODO: preferences flag?
        repository.load_mp3s(preferences.directory(),
                                        mp3_loaded_callback=self.on_mp3_loaded,
                                        mp3_image_loaded_callback=self.on_mp3_image_loaded,
                                        mp3s_loaded_callback=self.on_mp3s_loaded,
                                        mp3s_images_loaded_callback=self.on_mp3s_images_loaded)

        # Play
        self.ui.playPauseButton.clicked.connect(self.on_play_pause_button_clicked)
        self.ui.playArtist.set_underline_on_hover(True)
        self.ui.playArtist.clicked.connect(self.on_play_artist_clicked)
        self.ui.playAlbum.set_underline_on_hover(True)
        self.ui.playAlbum.clicked.connect(self.on_play_album_clicked)
        self.ui.playContainer.setVisible(False)
        self.ui.playBar.valueChangedManually.connect(self.on_play_bar_changed)
        self.ui.prevSongButton.clicked.connect(self.on_prev_song_button_clicked)
        self.ui.nextSongButton.clicked.connect(self.on_next_song_button_clicked)

        self.ui.playVolume.valueChangedManually.connect(self.on_play_volume_changed)
        volume = preferences.get_preference("volume")
        if volume is not None:
            self.ui.playVolume.set_value(volume)

        self.playing = PlayingInfo()
        self.playTimer = QTimer(self)
        self.playTimer.timeout.connect(self.on_play_timer_tick)

        # Restore geometry
        geometry, state = preferences.geometry_and_state()
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)

    def closeEvent(self, ev: QCloseEvent) -> None:
        debug("Closing window")
        # Save geometry
        preferences.set_geometry_and_state(self.saveGeometry(), self.saveState())

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

    def set_local_album_page(self):
        self.push_page(self.ui.localAlbumPage)

    def set_local_artist_page(self):
        self.push_page(self.ui.localArtistPage)

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
            if p == self.ui.localAlbumPage:
                return "local_album"
            if p == self.ui.localArtistsPage:
                return "local_artist"
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
        elif next_page == self.ui.localAlbumPage:
            pass
        elif next_page == self.ui.localArtistPage:
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
        self.ui.albumOpenButton.setVisible(False)

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
        self.current_local_album_mp3_group_leader = mp3

        # title
        self.ui.localAlbumTitle.setText(mp3.album or UNKNOWN_ALBUM)

        # artist
        self.ui.localAlbumArtist.setText(mp3.artist or UNKNOWN_ARTIST)

        # icon
        self.ui.localAlbumCover.setPixmap(make_pixmap_from_data(mp3.image, default=resources.COVER_PLACEHOLDER_PIXMAP))
        self.album_cover_data = mp3.image

        # tracks
        self.local_album_tracks_model.set(mp3)
        self.ui.localAlbumTracks.invalidate()

        # length
        self.ui.localAlbumSongCount.setText(
            f"{len(self.local_album_tracks_model.mp3s)} songs - "
            f"{millis_to_long_string(sum([mp3.length for mp3 in self.local_album_tracks_model.mp3s]))}")

        # switch page
        self.set_local_album_page()

        # favourite
        self.ui.localAlbumFavouriteButton.setIcon(
            resources.FAVOURITE_ICON
            if favourites.is_favourite(artist=mp3.artist, album=mp3.album) else
            resources.UNFAVOURITE_ICON)

    def open_mp3_release_group_remote(self, mp3: Mp3):
        # already fetched: open directly
        if mp3.fetched_release_group and mp3.release_group_id:
            self.open_release_group(get_release_group(mp3.release_group_id))
            return

        # fetch it by name
        self.current_release_group_id = None

        # title
        self.ui.albumTitle.setText(mp3.album)

        # artist
        self.ui.albumArtist.setText(mp3.artist or UNKNOWN_ARTIST)

        # icon
        self.ui.albumCover.setPixmap(make_pixmap_from_data(mp3.image, default=resources.COVER_PLACEHOLDER_PIXMAP))
        self.album_cover_data = mp3.image
        self.ui.albumCoverNumber.setText("")

        # download
        self.ui.albumDownloadAllButton.setEnabled(False)
        self.ui.albumDownloadAllButton.setText(f"Download missing songs")
        self.ui.albumDownloadStatus.setText("")
        self.ui.albumOpenButton.setVisible(False)

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
        self.ui.albumOpenButton.setVisible(False)

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
        self.current_local_artist_mp3_group_leader = mp3

        # title
        self.ui.localArtistName.setText(mp3.artist or UNKNOWN_ARTIST)

        # icon
        self.ui.localArtistCover.setPixmap(make_pixmap_from_data(mp3.image, default=resources.COVER_PLACEHOLDER_PIXMAP))
        self.album_cover_data = mp3.image

        # tracks
        self.local_artist_albums_model.set(mp3)
        self.ui.localArtistAlbums.invalidate()

        # switch page
        self.set_local_artist_page()

        # favourite
        self.ui.localArtistFavouriteButton.setIcon(
            resources.FAVOURITE_ICON
            if favourites.is_favourite(artist=mp3.artist) else
            resources.UNFAVOURITE_ICON)

    def open_mp3_artist_remote(self, mp3: Mp3):
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

        debug("Clearing search results")
        self.last_search_query = query
        self.search_results_model.results.clear()
        self.ui.searchResults.invalidate()

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

        if query != self.last_search_query:
            print(
                f"WARN: ignoring results for query: {query} since differs from current query: {self.last_search_query}")
            return

        if release_groups:
            for release_group in release_groups:
                self.search_results_model.results.append(release_group.id)
            self.ui.searchResults.invalidate()


    def on_search_artists_result(self, query, artists: List[Artist]):
        debug(f"on_search_artists_result(query={query}")

        if query != self.last_search_query:
            print(f"WARN: ignoring results for query: {query} since differs from current query: {self.last_search_query}")
            return

        if artists:
            for artist in artists:
                self.search_results_model.results.append(artist.id)
            self.ui.searchResults.invalidate()


    def on_release_group_releases_result(self, release_group_id: str, releases: List[Release]):
        debug(f"on_search_release_group_releases_result(release_group_id={release_group_id})")

        rg = get_release_group(release_group_id)
        if rg and self.current_release_group_id == rg.id:
            main_release_id = rg.main_release_id
            main_release = get_release(main_release_id)

            # link
            if rg.youtube_playlist_id:
                self.ui.albumLink.setText(youtube_playlist_id_to_youtube_url(rg.youtube_playlist_id))
            else:
                self.ui.albumLink.setText("")

            if main_release:
                self.album_tracks_model.release_id = main_release_id
                self.ui.albumTracks.invalidate()
                self.ui.albumYear.setText(rg.year())
                self.ui.albumSongCount.setText(f"{main_release.track_count()} songs - {millis_to_long_string(main_release.length())}")

                self.set_album_cover(release_group_id)

                self.update_album_download_widgets()

        self.ui.artistAlbums.update_row(release_group_id)

        # repository.search_release_youtube_tracks(main_release_id, self.on_release_youtube_tracks_result)


    def on_search_tracks_result(self, query, tracks: List[Track]):
        debug(f"on_search_tracks_result(query={query})")

        if query != self.last_search_query:
            print(
                f"WARN: ignoring results for query: {query} since differs from current query: {self.last_search_query}")
            return

        if tracks:
            for track in tracks:
                self.search_results_model.results.append(track.id)
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

    def on_local_artist_album_clicked(self, row: int):
        debug(f"on_local_artist_album_clicked(row={row})")
        album_group_leader = self.local_artist_albums_model.entry(row)
        self.open_mp3_release_group(album_group_leader)

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
        self.album_change_cover_empty_image_callback = self.set_album_cover_prev_prevent_loop
        release_group = get_release_group(self.current_release_group_id)
        self.album_change_cover_initial_index = release_group.preferred_front_cover_index
        self.set_album_cover_prev()


    def on_album_cover_next_button_clicked(self):
        debug("on_album_cover_next_button_clicked")
        self.album_change_cover_empty_image_callback = self.set_album_cover_next_prevent_loop
        release_group = get_release_group(self.current_release_group_id)
        self.album_change_cover_initial_index = release_group.preferred_front_cover_index
        self.set_album_cover_next()


    def set_album_cover_prev_prevent_loop(self, force=False):
        release_group = get_release_group(self.current_release_group_id)
        if not force and self.album_change_cover_initial_index == release_group.preferred_front_cover_index:
            return
        self.set_album_cover_prev()


    def set_album_cover_next_prevent_loop(self, force=False):
        release_group = get_release_group(self.current_release_group_id)
        if not force and self.album_change_cover_initial_index == release_group.preferred_front_cover_index:
            return
        self.set_album_cover_next()

    def set_album_cover_prev(self):
        self.handle_album_cover_change_request(direction="prev")


    def set_album_cover_next(self):
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

    def on_local_album_cover_double_clicked(self, ev: QMouseEvent):
        debug("on_local_album_cover_double_clicked")
        image_preview_window = ImagePreviewWindow()
        image_preview_window.set_image(self.album_cover_data)
        image_preview_window.exec()

    def on_artist_image_double_clicked(self, ev: QMouseEvent):
        debug("on_artist_image_double_clicked")
        image_preview_window = ImagePreviewWindow()
        image_preview_window.set_image(self.artist_cover_data)
        image_preview_window.exec()

    def on_local_artist_image_double_clicked(self, ev: QMouseEvent):
        debug("on_local_artist_image_double_clicked")
        image_preview_window = ImagePreviewWindow()
        image_preview_window.set_image(self.artist_cover_data)
        image_preview_window.exec()


    def on_local_album_track_clicked(self, row: int):
        pass

    def on_local_album_artist_clicked_2(self):
        debug("on_local_album_artist_clicked_2")
        self.open_mp3_artist(self.current_local_album_mp3_group_leader)

    def on_release_group_youtube_tracks_result(self, release_group_id: str, yttracks: List[YtTrack]):
        debug("on_release_group_youtube_tracks_result")

        # fetch missing ones
        release_group = get_release_group(release_group_id)
        release = release_group.main_release()

        missing = 0
        for t in release.tracks():
            if not t.fetched_youtube_track:
                missing += 1
                repository.search_track_youtube_track(t.id, self.on_track_youtube_track_result)

        if missing:
            debug(f"After release tracks fetching there was still {missing} "
                  f"missing tracks missing youtube video, searching now")

        self.handle_youtube_tracks_update(release.id)

        if self.current_release_group_id == release.release_group_id:
            self.ui.albumLink.setText(youtube_playlist_id_to_youtube_url(release_group.youtube_playlist_id))


    def on_track_youtube_track_result(self, track_id: str, yttrack: YtTrack):
        track = get_track(track_id)
        # self.ui.albumTracks.update_row(track_id) # would be more precise
        self.handle_youtube_tracks_update(track.release_id)


    def on_track_link_button_clicked(self, row: int):
        debug("on_track_link_button_clicked")
        track_id = self.album_tracks_model.entry(row)
        track = get_track(track_id)
        video_id = get_youtube_track(track.youtube_track_id).video_id if track.youtube_track_id else None
        edit_link_window = EditLinkWindow(ytcommons.youtube_video_id_to_youtube_url(video_id))
        edit_link_window.exec()
        if edit_link_window.link:
            debug(f"New link set for track {track_id}: {edit_link_window.link}")
            video_id = ytcommons.youtube_url_to_video_id(edit_link_window.link)
            if video_id:
                repository.set_track_youtube_video_id(track_id, video_id)
            else:
                print("WARN: invalid youtube URL")
                QMessageBox.warning(self, "Invalid YouTube URL", f"Invalid YouTube URL")



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
        verified_only = self.ui.albumDownloadAllVerifiedCheck.isChecked()
        missing_downloadable = 0
        verified = 0
        for track in tracks:
            if track.fetched_youtube_track and track.youtube_track_id:
                if track.youtube_track_is_official:
                    verified += 1
                if not track.is_locally_available() and not track.downloading and \
                        (not verified_only or track.youtube_track_is_official):
                    missing_downloadable += 1

        self.ui.albumDownloadAllButton.setEnabled(missing_downloadable > 0)
        if missing_downloadable > 0:
            self.ui.albumDownloadAllButton.setText(f"Download missing songs ({missing_downloadable})")
        else:
            self.ui.albumDownloadAllButton.setText(f"Download missing songs")

        # Download missing tracks status
        self.ui.albumDownloadStatus.setText(f"Verified songs: {verified}/{release.track_count()}")
        self.ui.albumDownloadStatus.setToolTip("\n".join([f'{t.title} [{"verified" if t.youtube_track_is_official else "not verified"}]' for t in tracks]))

        self.ui.albumOpenButton.setVisible(True)
        self.ui.albumOpenButton.setToolTip("Open album in YouTube")


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

        # TODO: skipping the update in this way is a little bit superficial
        # at least the stuff should be invalidated when reentering download/album/...
        cur_page = self.pages_stack[-1]

        if cur_page == self.ui.downloadsPage:
            self.ui.queuedDownloads.update_row(video_id)

        if cur_page == self.ui.albumPage:
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
        self.local_songs_model.reload()
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

        error_managed = False

        # if "age" in error_msg:
        #     debug("Age problem, eventually showing sign in window")
        #     # Show sign in alert
        #     if not ytdownloader.is_signed_in():
        #         error_managed = True
        #         sign_in_window = YouTubeSignInWindow()
        #         sign_in_window.exec()
        #         if ytdownloader.is_signed_in():
        #             # Now we are signed in, try again
        #             debug("Now we are signed in, trying again to download song")
        #             if down["user_data"]["type"] == "official":
        #                 track_id = down["user_data"]["id"]
        #                 self.do_download_youtube_track(track_id)
        #             elif down["user_data"]["type"] == "manual":
        #                 video_id = down["user_data"]["id"]
        #                 self.do_download_youtube_track_manual(video_id)

        if not error_managed:
            artist = down["artist"]
            album = down["album"]
            song = down["song"]
            QMessageBox.warning(self, "Download failed",
                                f"Download of {artist} - {album} - {song} failed\n"
                                f"Reason: {error_msg}",
                                QMessageBox.Ok)

    def update_downloads_count(self):
        queued_count = ytdownloader.download_count()
        finished_count = ytdownloader.finished_download_count()
        self.ui.downloadsPageButton.setText(f"Downloads ({queued_count})" if queued_count else "Downloads")
        self.ui.downloadsTabs.setTabText(DOWNLOADS_TABS_QUEUED_INDEX, f"Queue ({queued_count})" if queued_count else "Queue")
        self.ui.downloadsTabs.setTabText(DOWNLOADS_TABS_COMPLETED_INDEX, f"Completed ({finished_count})" if finished_count else "Completed")

    def on_download_missing_album_tracks_clicked(self):
        verified_only = self.ui.albumDownloadAllVerifiedCheck.isChecked()
        debug(f"on_download_missing_album_tracks_clicked (verified_only={verified_only})")
        rg = get_release_group(self.current_release_group_id)
        for track in rg.main_release().tracks():
            if not track.is_locally_available() and not track.downloading:
                if not verified_only or track.youtube_track_is_official:
                    self.do_download_youtube_track(track.id)

    def on_download_missing_album_tracks_verified_check_changed(self):
        debug(f"on_download_missing_album_tracks_verified_check_changed")
        self.update_album_download_widgets()

    def on_open_album_button_clicked(self):
        debug("on_open_album_button_clicked")
        rg = get_release_group(self.current_release_group_id)
        if rg.youtube_playlist_id:
            open_url(ytcommons.youtube_playlist_id_to_youtube_url(rg.youtube_playlist_id))
        else:
            print(f"WARN: no playlist id available for release group {rg.title}")

    def on_local_album_open_remote_button_clicked(self):
        debug("on_local_album_open_remote_button_clicked")
        self.open_mp3_release_group_remote(self.current_local_album_mp3_group_leader)

    def on_local_artist_open_remote_button_clicked(self):
        debug("on_local_artist_open_remote_button_clicked")
        self.open_mp3_artist_remote(self.current_local_artist_mp3_group_leader)

    def on_local_album_random_play_button_clicked(self):
        artist = self.current_local_album_mp3_group_leader.artist
        album = self.current_local_album_mp3_group_leader.album
        queue = [mp3 for mp3 in localsongs.mp3s if mp3.artist == artist and mp3.album == album]
        random.shuffle(queue)
        self.play(0, queue)

    def on_local_album_favourite_button_clicked(self):
        artist = self.current_local_album_mp3_group_leader.artist
        album = self.current_local_album_mp3_group_leader.album
        is_favourite = favourites.is_favourite(artist=artist, album=album)
        next_is_favourite = not is_favourite

        favourites.set_favourite(artist=artist, album=album, song=None, favourite=next_is_favourite)

        if next_is_favourite:
            self.ui.localAlbumFavouriteButton.setIcon(resources.FAVOURITE_ICON)
        else:
            self.ui.localAlbumFavouriteButton.setIcon(resources.UNFAVOURITE_ICON)

    def on_local_artist_random_play_button_clicked(self):
        artist = self.current_local_artist_mp3_group_leader.artist
        queue = [mp3 for mp3 in localsongs.mp3s if mp3.artist == artist]
        random.shuffle(queue)
        self.play(0, queue)

    def on_local_artist_favourite_button_clicked(self):
        artist = self.current_local_artist_mp3_group_leader.artist
        is_favourite = favourites.is_favourite(artist=artist)
        next_is_favourite = not is_favourite

        favourites.set_favourite(artist=artist, album=None, song=None, favourite=next_is_favourite)
        if next_is_favourite:
            self.ui.localArtistFavouriteButton.setIcon(resources.FAVOURITE_ICON)
        else:
            self.ui.localArtistFavouriteButton.setIcon(resources.UNFAVOURITE_ICON)

    def on_local_songs_random_play_button_clicked(self):
        queue = list(localsongs.mp3s)
        random.shuffle(queue)
        self.play(0, queue)

    def do_download_youtube_track(self, track_id):
        repository.download_youtube_track(track_id,
                                          queued_callback=self.on_youtube_track_download_queued,
                                          started_callback=self.on_youtube_track_download_started,
                                          progress_callback=self.on_youtube_track_download_progress,
                                          finished_callback=self.on_youtube_track_download_finished,
                                          canceled_callback=self.on_youtube_track_download_canceled,
                                          error_callback=self.on_youtube_track_download_error)

    def do_download_youtube_track_manual(self, video_id):
        repository.download_youtube_track(video_id,
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

    def on_mp3_image_loaded(self, mp3: Mp3):
        pass

    def on_mp3s_images_loaded(self):
        debug("Reloading mp3s model")
        # self.ui.localSongs.invalidate()
        self.reload_local_songs_artists_albums()

    def on_action_refresh(self):
        localsongs.clear_mp3s()

        self.reload_local_songs_artists_albums()

        self.update_local_song_count()
        repository.load_mp3s(preferences.directory(),
                                        mp3_loaded_callback=self.on_mp3_loaded,
                                        mp3_image_loaded_callback=self.on_mp3_image_loaded,
                                        mp3s_loaded_callback=self.on_mp3s_loaded,
                                        mp3s_images_loaded_callback=self.on_mp3s_images_loaded)

    def on_action_reload(self):
        cache.clear_localsongs()
        self.on_action_refresh()

    def reload_local_songs_artists_albums(self):
        self.local_songs_model.beginResetModel()
        self.local_songs_model.reload()
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
        mp3 = self.local_songs_model.entry(row)
        debug(f"on_local_song_artist_clicked: {mp3}")
        self.open_mp3_artist(mp3)

    def on_local_song_album_clicked(self, row: int):
        mp3 = self.local_songs_model.entry(row)
        debug(f"on_local_song_album_clicked: {mp3}")
        self.open_mp3_release_group(mp3)

    def on_local_song_clicked(self, row: int):
        mp3 = self.local_songs_model.entry(row)
        debug(f"on_local_song_clicked: {mp3}")

    def on_local_song_double_clicked(self, row: int):
        mp3 = self.local_songs_model.entry(row)
        debug(f"on_local_song_double_clicked: {mp3}")
        if mp3.path:
            self.play(row, list(self.local_songs_model.localsongs))

    def on_finished_download_double_clicked(self, row: int):
        debug("on_finished_download_double_clicked")
        down = self.finished_downloads_model.entry(row)
        if down:
            # debug(f"Associated download: {down}")
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

    def on_local_album_clicked(self, row: int):
        debug("on_local_album_clicked")
        mp3_group_leader = self.local_albums_model.entry(row)
        self.open_mp3_release_group(mp3_group_leader)

    def on_local_album_artist_clicked(self, row: int):
        debug("on_local_album_artist_clicked")
        mp3_group_leader = self.local_albums_model.entry(row)
        self.open_mp3_artist(mp3_group_leader)

    def on_track_double_clicked(self, row: int):
        debug("on_track_double_clicked")
        track_id = self.album_tracks_model.entry(row)
        self.play(row, list(get_release(self.album_tracks_model.release_id).tracks()))

    def on_local_track_double_clicked(self, row: int):
        debug("on_local_track_double_clicked")
        mp3 = self.local_album_tracks_model.entry(row)
        self.play(row, list(self.local_album_tracks_model.mp3s))

    def play(self, index: int, queue=None):
        if queue is not None:
            self.playing.queue = queue

        if index < 0 or index >= len(self.playing.queue):
            debug("Nothing to play")
            return

        self.playing.index = index
        song = self.playing.queue[index]

        if isinstance(song, Mp3):
            self.play_mp3(song)
        elif isinstance(song, Track):
            self.play_track(song)

    def play_mp3(self, mp3: Mp3):
        self.ui.playContainer.setVisible(False)

        self.ui.playCover.setPixmap(make_pixmap_from_data(mp3.image, default=resources.COVER_PLACEHOLDER_PIXMAP))
        self.ui.playTitle.setText(mp3.title())
        self.ui.playArtist.setText(mp3.artist or UNKNOWN_ARTIST)
        self.ui.playAlbum.setText(mp3.album or UNKNOWN_ALBUM)

        self.ui.playBar.set_value(0)
        self.ui.playCurrentTime.setText(millis_to_short_string(0))
        self.ui.playMaxTime.setText(millis_to_short_string(mp3.length))

        self.play_audio(str(mp3.path))

    def play_track(self, track: Track):
        local_mp3, local_mp3_idx = track.get_local_ext()
        if local_mp3:
            # play locally if available
            self.play_mp3(local_mp3)
            return

        # play from url
        self.ui.playContainer.setVisible(False)

        rg = track.release().release_group()
        self.ui.playCover.setPixmap(make_pixmap_from_data(rg.preferred_front_cover(), default=resources.COVER_PLACEHOLDER_PIXMAP))
        self.ui.playTitle.setText(track.title)
        self.ui.playArtist.setText(rg.artists_string() or UNKNOWN_ARTIST)
        self.ui.playAlbum.setText(rg.title or UNKNOWN_ALBUM)

        self.ui.playBar.set_value(0)
        self.ui.playCurrentTime.setText(millis_to_short_string(0))
        self.ui.playMaxTime.setText(millis_to_short_string(track.length))

        def track_streams_fetched(_1, _2):
            yttrack = get_youtube_track(track.youtube_track_id)

            audios = sorted([s for s in yttrack.streams if s["type"] == "audio"], key=lambda s: s["size"])
            if audios:
                self.play_audio(audios[0]["url"])

        repository.fetch_youtube_track_streams(track.id, track_streams_fetched)

    def play_audio(self, audio_url_or_path: str):
        audioplayer.set_time(0)
        audioplayer.open_stream(audio_url_or_path)
        audioplayer.play()

        self.ui.playContainer.setVisible(True)
        self.ui.playPauseButton.setIcon(resources.PAUSE_ICON)
        self.playTimer.start(200)

    def on_play_pause_button_clicked(self):
        if not audioplayer.stream_is_open():
            print("WARN: stream is not loaded yet")
            return

        if audioplayer.is_playing():
            audioplayer.pause()
            self.ui.playPauseButton.setIcon(resources.PLAY_ICON)
        elif audioplayer.is_paused():
            audioplayer.play()
            self.playTimer.start(200)
            self.ui.playPauseButton.setIcon(resources.PAUSE_ICON)
        elif audioplayer.is_ended():
            audioplayer.set_time(0)
            audioplayer.play()
            self.ui.playPauseButton.setIcon(resources.PAUSE_ICON)
            self.update_play_progress()
        else:
            print(f"WARN: unexpected audio player state: {audioplayer.get_state()}")

    def on_play_artist_clicked(self):
        in_play = self.playing.in_play()
        if isinstance(in_play, Mp3):
            self.open_mp3_artist(in_play)
        elif isinstance(in_play, Track):
            # TODO: more than an artist
            self.open_artist(in_play.release().release_group().artists()[0])

    def on_play_album_clicked(self):
        in_play = self.playing.in_play()
        if isinstance(in_play, Mp3):
            self.open_mp3_release_group(in_play)
        elif isinstance(in_play, Track):
            self.open_release_group(in_play.release().release_group())

    def on_play_timer_tick(self):
        self.update_play_progress()

    def update_play_progress(self):
        if audioplayer.is_playing():
            t = audioplayer.get_time()
            self.ui.playCurrentTime.setText(millis_to_short_string(t))
            try:
                playbar_value = int(100 * t / self.playing.in_play().length)
                self.ui.playBar.set_value(playbar_value)
            except:
                self.ui.playBar.set_value(0)
        elif audioplayer.is_paused():
            self.playTimer.stop()
        elif audioplayer.is_ended():
            self.playTimer.stop()
            self.ui.playPauseButton.setIcon(resources.PLAY_ICON)
            self.ui.playCurrentTime.setText(millis_to_short_string(0))
            self.ui.playBar.set_value(0)
            self.play_next()


    def play_by_offset(self, delta):
        debug("play_next")
        self.play(self.playing.index + delta)

    def play_next(self):
        debug("play_next")
        self.play_by_offset(1)

    def play_prev(self):
        debug("play_prev")
        self.play_by_offset(-1)

    def on_play_bar_changed(self):
        # t : length = value : 100
        t = rangify(0, int(self.ui.playBar.value() * self.playing.in_play().length / 100), self.playing.in_play().length)
        audioplayer.set_time(t)
        self.update_play_progress()

    def on_play_volume_changed(self):
        volume = self.ui.playVolume.value()
        audioplayer.set_volume(volume)
        preferences.set_preference("volume", volume)

    def on_prev_song_button_clicked(self):
        self.play_prev()

    def on_next_song_button_clicked(self):
        self.play_next()

    def on_album_link_button_clicked(self):
        debug("on_album_link_button_clicked")
        self.ui.albumLinkButton.setVisible(False)
        self.ui.albumLinkContainer.setVisible(True)

    def on_album_link_ok_button_clicked(self):
        debug("on_album_link_ok_button_clicked")
        self.ui.albumLinkButton.setVisible(True)
        self.ui.albumLinkContainer.setVisible(False)
        playlist_id = youtube_url_to_playlist_id(self.ui.albumLink.text())
        if not playlist_id:
            print("WARN: invalid youtube url")
            QMessageBox.warning(self, "Invalid URL",
                                "Invalid YouTube URL",
                                QMessageBox.Ok)
            return

        repository.set_release_group_playlist_id(self.current_release_group_id, playlist_id,
                                                 self.on_release_group_releases_result, self.on_release_group_youtube_tracks_result)

    def on_album_link_cancel_button_clicked(self):
        debug("on_album_link_cancel_button_clicked")
        self.ui.albumLinkButton.setVisible(True)
        self.ui.albumLinkContainer.setVisible(False)

    def on_show_album_tracks_youtube_titles_check_changed(self):
        debug("on_show_album_tracks_youtube_titles_check_changed")
        self.ui.albumTracks.set_show_youtube_titles(self.ui.showYouTubeTitlesCheck.isChecked())

    def on_album_open_local_button_clicked(self):
        debug("on_album_open_local_button_clicked")
        album = get_release_group(self.current_release_group_id)
        for mp3 in localsongs.mp3s:
            if mp3.artist and mp3.artist.lower() == album.artists_string().lower() and mp3.album and mp3.album.lower() == album.title.lower():
                self.open_mp3_release_group(mp3)
                return
        print(f"WARN: album '{album.title}' not locally available")

    def on_artist_open_local_button_clicked(self):
        debug("on_artist_open_local_button_clicked")
        artist = get_artist(self.current_artist_id)
        for mp3 in localsongs.mp3s:
            if mp3.artist and mp3.artist.lower() == artist.name.lower():
                self.open_mp3_artist(mp3)
                return
        print(f"WARN: artist '{artist.name}' not locally available")

    def on_local_songs_filter_changed(self):
        filter_text = self.ui.localSongsFilter.text()
        debug(f"on_local_songs_filter_changed({filter_text})")
        self.local_songs_proxy_model.setFilterRegularExpression(QRegularExpression(filter_text, QRegularExpression.CaseInsensitiveOption))


    def on_local_artists_filter_changed(self):
        filter_text = self.ui.localArtistsFilter.text()
        debug(f"on_local_artists_filter_changed({filter_text})")
        self.local_artists_proxy_model.setFilterRegularExpression(QRegularExpression(filter_text, QRegularExpression.CaseInsensitiveOption))


    def on_local_albums_filter_changed(self):
        filter_text = self.ui.localAlbumsFilter.text()
        debug(f"on_local_albums_filter_changed({filter_text})")
        self.local_albums_proxy_model.setFilterRegularExpression(QRegularExpression(filter_text, QRegularExpression.CaseInsensitiveOption))

    def on_auto_download_queued_check_changed(self):
        debug(f"on_auto_download_queued_check_changed={self.ui.autoDownloadQueuedCheck.isChecked()}")
        ytdownloader.set_auto_download(self.ui.autoDownloadQueuedCheck.isChecked())

    def on_local_artists_favourite_clicked(self, row: int):
        mp3 = self.local_artists_model.entry(row)
        artist = mp3.artist
        debug(f"on_local_artists_favourite_clicked(artist={artist})")

        is_favourite = favourites.is_favourite(artist=artist)
        next_is_favourite = not is_favourite

        favourites.set_favourite(artist=artist, album=None, song=None, favourite=next_is_favourite)

    def on_local_albums_favourite_clicked(self, row: int):
        mp3 = self.local_albums_model.entry(row)
        artist = mp3.artist
        album = mp3.album
        debug(f"on_local_albums_favourite_clicked(artist={artist})")

        is_favourite = favourites.is_favourite(artist=artist, album=album)
        next_is_favourite = not is_favourite

        favourites.set_favourite(artist=artist, album=album, song=None, favourite=next_is_favourite)

    def on_local_artist_favourite_album_button_clicked(self, row: int):
        artist = self.local_artist_albums_model.artist
        album = self.local_artist_albums_model.entry(row).album

        debug(f"on_local_albums_favourite_clicked(artist={artist}, album={album})")

        is_favourite = favourites.is_favourite(artist=artist, album=album)
        next_is_favourite = not is_favourite

        favourites.set_favourite(artist=artist, album=album, song=None, favourite=next_is_favourite)

        self.ui.localArtistAlbums.update_row(self.local_artist_albums_model.entry(row))



