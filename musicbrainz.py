from statistics import mean
from typing import Optional, List

import musicbrainzngs as mb

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool

from cache import COVER_CACHE
from entities import YtTrack
from log import debug
from utils import j


class MbTrack:
    def __init__(self, mb_track, release_id):
        self.id = mb_track["recording"]["id"]
        self.length = int(mb_track["recording"]["length"]) if "length" in mb_track["recording"] else 0
        self.title = mb_track["recording"]["title"]
        self.track_number = mb_track["position"]
        self.youtube_track: Optional[YtTrack] = None
        self.release_id = release_id


class MbRelease:
    def __init__(self, mb_release):
        self.id: str = mb_release["id"]
        self.title: str = mb_release["title"]
        self.release_group_id = mb_release["release-group"]["id"]

        # TODO: keep only ids
        self.tracks = [MbTrack(track, mb_release["id"]) for track in mb_release["medium-list"][0]["track-list"]]

class MbReleaseGroup:
    def __init__(self, mb_release_group):
        self.id: str = mb_release_group["id"]
        self.title: str = mb_release_group["title"]
        try:
            self.year: str = mb_release_group["first-release-date"].split("-")[0]
        except:
            self.year = "Unknown"
        self.score: int = int(mb_release_group.get("ext-score", 0))
        self.artists = []
        self.releases = []
        # TODO: keep only ids
        if "artist-credit" in mb_release_group:
            self.artists = [{
                "id": artist_credit["artist"]["id"],
                "name": artist_credit["artist"]["name"],
                "aliases": [alias["alias"] for alias in artist_credit["artist"].get("aliases-list", [])]
            }  for artist_credit in mb_release_group["artist-credit"] if isinstance(artist_credit, dict)]
        if "release-list" in mb_release_group:
            self.releases = [{
                "id": release["id"],
                "title": release["title"],
            }  for release in mb_release_group["release-list"]]
        self.main_release_id = None
        # self.images = Images()

    def artists_string(self):
        if not self.artists:
            return "Unknown Artist"
        return ", ".join(artist["name"] for artist in self.artists)

    # def cover(self):
    #     return COVER_CACHE.get(self.id)

class MbArtist:
    def __init__(self, mb_artist):
        self.id = mb_artist["id"]
        self.name = mb_artist["name"]

        self.aliases = []
        if "aliases-list" in mb_artist:
            self.aliases = [alias["alias"] for alias in mb_artist["aliases-list"]]

        # TODO: keep only ids
        self.release_groups = []
        if "release-group-list" in mb_artist:
            self.release_groups = [
                MbReleaseGroup(release_group) for release_group in mb_artist["release-group-list"]
            ]

        self.urls = {}
        if "url-relation-list" in mb_artist:
            for url in mb_artist["url-relation-list"]:
                self.urls[url["type"]] = url["target"]

        # self.images = Images()

# ============= SEARCH ARTISTS ============
# Search the artists for a given query
# =========================================

class SearchArtistsSignals(QObject):
    finished = pyqtSignal(str, list)

class SearchArtistsRunnable(QRunnable):
    def __init__(self, query, limit):
        super().__init__()
        self.signals = SearchArtistsSignals()
        self.query = query
        self.limit = limit

    @pyqtSlot()
    def run(self) -> None:
        if not self.query:
            return
        debug(f"[SearchArtistsRunnable (query='{self.query}']")

        debug(f"MUSICBRAINZ: search_artists: '{self.query}'")
        result = mb.search_artists(
            self.query, limit=self.limit
        )["artist-list"]
        debug(
            "=== search_artists ==="
            f"{j(result)}"
            "======================"
        )

        artists = [MbArtist(a) for a in result]

        self.signals.finished.emit(self.query, artists)

def search_artists(query, callback, limit):
    runnable = SearchArtistsRunnable(query, limit)
    runnable.signals.finished.connect(callback)
    QThreadPool.globalInstance().start(runnable)


# ========== SEARCH RELEASE GROUP ==========
# Search the release groups for a given query
# ==========================================

class SearchReleaseGroupsSignals(QObject):
    finished = pyqtSignal(str, list)

class SearchReleaseGroupsRunnable(QRunnable):
    def __init__(self, query, limit):
        super().__init__()
        self.signals = SearchReleaseGroupsSignals()
        self.query = query
        self.limit = limit

    @pyqtSlot()
    def run(self) -> None:
        if not self.query:
            return
        debug(f"[SearchReleaseGroupsRunnable (query='{self.query}']")

        debug(f"MUSICBRAINZ: search_release_groups: '{self.query}'")
        result = mb.search_release_groups(
            self.query, limit=self.limit, primarytype="Album", status="Official"
        )["release-group-list"]
        debug(
            "=== search_release_groups ==="
            f"{j(result)}"
            "======================"
        )
        release_groups = [MbReleaseGroup(release_group) for release_group in result
                          if "primary-type" in release_group and release_group["primary-type"] in ["Album", "EP"]]

        self.signals.finished.emit(self.query, release_groups)

def search_release_groups(query, callback, limit):
    runnable = SearchReleaseGroupsRunnable(query, limit)
    runnable.signals.finished.connect(callback)
    QThreadPool.globalInstance().start(runnable)


# ======= FETCH RELEASE GROUP COVER ======
# Fetch the cover of a release group
# ========================================

class FetchReleaseGroupCoverSignals(QObject):
    finished = pyqtSignal(str, bytes)


class FetchReleaseGroupCoverRunnable(QRunnable):
    # size can be: “250”, “500”, “1200” or None.
    # If it is None, the largest available picture will be downloaded.
    def __init__(self, release_group_id: str, size="250"):
        super().__init__()
        self.signals = FetchReleaseGroupCoverSignals()
        self.release_group_id = release_group_id
        self.size = size

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[FetchReleaseGroupCoverRunnable (release_group_id='{self.release_group_id}'], size={self.size})")

        try:
            debug(f"MUSICBRAINZ: get_release_group_image_front: '{self.release_group_id}'")
            image = mb.get_release_group_image_front(self.release_group_id, size=self.size)
            self.signals.finished.emit(self.release_group_id, image)
        except mb.ResponseError:
            print(f"WARN: no image for release group '{self.release_group_id}'")


def fetch_release_group_cover(release_group_id, callback):
    runnable = FetchReleaseGroupCoverRunnable(release_group_id)
    runnable.signals.finished.connect(callback)
    QThreadPool.globalInstance().start(runnable)


# ======= FETCH RELEASE GROUP RELEASES RUNNABLE ========
# Fetch the more appropriate release of a release group
# =====================================================

class FetchReleaseGroupReleasesSignals(QObject):
    finished = pyqtSignal(str, list)


class FetchReleaseGroupReleasesRunnable(QRunnable):
    def __init__(self, release_group_id: str):
        super().__init__()
        self.signals = FetchReleaseGroupReleasesSignals()
        self.release_group_id = release_group_id

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[FetchReleaseGroupReleasesRunnable (release_group_id='{self.release_group_id}'])")

        # Fetch all the releases and releases tracks for the release groups
        result = mb.browse_releases(
            release_group=self.release_group_id, includes=["recordings", "recording-rels", "release-groups"]
        )["release-list"]
        debug(
            "=== browse_releases ==="
            f"{j(result)}"
            "======================"
        )

        releases = [MbRelease(release) for release in result]

        self.signals.finished.emit(self.release_group_id, releases)

        # TODO not here

        # main_release = MbRelease(self.release_group_id, result[main_release_index])


def fetch_release_group_releases(release_group_id, callback):
    runnable = FetchReleaseGroupReleasesRunnable(release_group_id)
    runnable.signals.finished.connect(callback)
    QThreadPool.globalInstance().start(runnable)

# ============ FETCH ARTIST =============
# Fetch the details of the given artist
# =======================================

class FetchArtistSignals(QObject):
    finished = pyqtSignal(str, MbArtist)

class FetchArtistRunnable(QRunnable):
    def __init__(self, artist_id: str):
        super().__init__()
        self.signals = FetchArtistSignals()
        self.artist_id = artist_id

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[FetchArtistRunnable (artist='{self.artist_id}'])")

        # Fetch all the releases and releases tracks for the release groups
        # result = mb.get_artist_by_id(self.artist_id, includes=["aliases", "release-groups", "url-rels", "annotation", "releases", "isrcs"])
        result = mb.get_artist_by_id(
            self.artist_id,
            includes=["aliases", "release-groups", "releases", "url-rels"]
        )["artist"]
        debug(
            "=== get_artist_by_id ==="
            f"{j(result)}"
            "======================"
        )

        self.signals.finished.emit(self.artist_id, MbArtist(result))

def fetch_artist(artist_id, callback):
    runnable = FetchArtistRunnable(artist_id)
    runnable.signals.finished.connect(callback)
    QThreadPool.globalInstance().start(runnable)
