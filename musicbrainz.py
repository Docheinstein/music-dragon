from typing import Optional

import musicbrainzngs as mb
from PyQt5.QtCore import pyqtSignal, pyqtSlot

import workers
from log import debug
from utils import j
from workers import Worker
from youtube import YtTrack


def initialize():
    mb.set_useragent("MusicDragon", "0.1")

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
        self.tracks = [MbTrack(track, mb_release["id"]) for track in mb_release["medium-list"][0]["track-list"]]

class MbReleaseGroup:
    def __init__(self, mb_release_group):
        self.id: str = mb_release_group["id"]
        self.title: str = mb_release_group["title"]
        self.date = mb_release_group.get("first-release-date", "")
        self.score: int = int(mb_release_group.get("ext-score", 0))

        self.artists = []
        self.releases = []

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

class MbArtist:
    def __init__(self, mb_artist):
        self.id = mb_artist["id"]
        self.name = mb_artist["name"]
        self.aliases = []
        self.release_groups = []
        self.urls = {}

        if "aliases-list" in mb_artist:
            self.aliases = [alias["alias"] for alias in mb_artist["aliases-list"]]

        if "release-group-list" in mb_artist:
            for release_group in mb_artist["release-group-list"]:
                mb_release_group = MbReleaseGroup(release_group)
                # TODO: what if there is more than an artist?
                mb_release_group.artists.append({
                    "id": self.id,
                    "name": self.name,
                    "aliases": self.aliases
                })
                self.release_groups.append(mb_release_group)

        if "url-relation-list" in mb_artist:
            for url in mb_artist["url-relation-list"]:
                self.urls[url["type"]] = url["target"]



# ============= SEARCH ARTISTS ============
# Search the artists for a given query
# =========================================

class SearchArtistsWorker(Worker):
    result = pyqtSignal(str, list)

    def __init__(self, query, limit):
        super().__init__()
        self.query = query
        self.limit = limit

    @pyqtSlot()
    def run(self):
        if not self.query:
            return
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

        self.result.emit(self.query, artists)
        self.finish()

def search_artists(query, callback, limit):
    worker = SearchArtistsWorker(query, limit)
    worker.result.connect(callback)
    workers.execute(worker)


# ========== SEARCH RELEASE GROUP ==========
# Search the release groups for a given query
# ==========================================

class SearchReleaseGroupsWorker(Worker):
    result = pyqtSignal(str, list)

    def __init__(self, query, limit):
        super().__init__()
        self.query = query
        self.limit = limit

    @pyqtSlot()
    def run(self):
        if not self.query:
            return
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

        self.result.emit(self.query, release_groups)
        self.finish()

def search_release_groups(query, callback, limit):
    worker = SearchReleaseGroupsWorker(query, limit)
    worker.result.connect(callback)
    workers.execute(worker)


# ======= FETCH RELEASE GROUP COVER ======
# Fetch the cover of a release group
# ========================================

class FetchReleaseGroupCoverWorker(Worker):
    result = pyqtSignal(str, bytes)

    # size can be: “250”, “500”, “1200” or None.
    # If it is None, the largest available picture will be downloaded.
    def __init__(self, release_group_id: str, size="250"):
        super().__init__()
        self.release_group_id = release_group_id
        self.size = size

    @pyqtSlot()
    def run(self):
        try:
            debug(f"MUSICBRAINZ: get_release_group_image_front: '{self.release_group_id}'")
            image = mb.get_release_group_image_front(self.release_group_id, size=self.size)
            debug(f"MUSICBRAINZ: get_release_group_image_front: '{self.release_group_id}' retrieved")
            self.result.emit(self.release_group_id, image)
        except mb.ResponseError:
            print(f"WARN: no image for release group '{self.release_group_id}'")
            self.result.emit(self.release_group_id, bytes())
        self.finish()


def fetch_release_group_cover(release_group_id, callback):
    worker = FetchReleaseGroupCoverWorker(release_group_id)
    worker.result.connect(callback)
    workers.execute(worker)


# ======= FETCH RELEASE GROUP RELEASES RUNNABLE ========
# Fetch the more appropriate release of a release group
# =====================================================

class FetchReleaseGroupReleasesWorker(Worker):
    result = pyqtSignal(str, list)

    def __init__(self, release_group_id: str):
        super().__init__()
        self.release_group_id = release_group_id

    @pyqtSlot()
    def run(self):
        # Fetch all the releases and releases tracks for the release groups
        debug(f"MUSICBRAINZ: browse_releases: '{self.release_group_id}'")
        result = mb.browse_releases(
            release_group=self.release_group_id,
            includes=["recordings", "recording-rels", "release-groups", "media"]
        )["release-list"]
        debug(
            "=== browse_releases ==="
            f"{j(result)}"
            "======================"
        )

        releases = [MbRelease(release) for release in result]

        # # TODO remove
        # try:
        #     debug(f"MUSICBRAINZ: get_release_group_image_list: '{self.release_group_id}'")
        #     result = mb.get_release_group_image_list(self.release_group_id)
        #     debug(
        #         "=== get_release_group_image_list ==="
        #         f"{j(result)}"
        #         "======================"
        #     )
        # except mb.ResponseError:
        #     print(f"WARN: no image list for release group '{self.release_group_id}'")
        #
        # for release in releases:
        #     try:
        #         debug(f"MUSICBRAINZ: get_image_list: '{release.id}'")
        #         result = mb.get_image_list(release.id)
        #         debug(
        #             "=== get_image_list ==="
        #             f"{j(result)}"
        #             "======================"
        #         )
        #     except mb.ResponseError:
        #         print(f"WARN: no image list for release group '{release.id}'")
        #

        self.result.emit(self.release_group_id, releases)
        self.finish()


def fetch_release_group_releases(release_group_id, callback):
    worker = FetchReleaseGroupReleasesWorker(release_group_id)
    worker.result.connect(callback)
    workers.execute(worker)


# ============ FETCH ARTIST =============
# Fetch the details of the given artist
# =======================================

class FetchArtistWorker(Worker):
    result = pyqtSignal(str, MbArtist)

    def __init__(self, artist_id: str):
        super().__init__()
        self.artist_id = artist_id

    @pyqtSlot()
    def run(self):
        # Fetch all the releases and releases tracks for the release groups
        # result = mb.get_artist_by_id(self.artist_id, includes=["aliases", "release-groups", "url-rels", "annotation", "releases", "isrcs"])
        debug(f"MUSICBRAINZ: get_artist_by_id: '{self.artist_id}'")
        result = mb.get_artist_by_id(
            self.artist_id,
            includes=["aliases", "release-groups", "releases", "url-rels"]
        )["artist"]
        debug(
            "=== get_artist_by_id ==="
            f"{j(result)}"
            "======================"
        )

        self.result.emit(self.artist_id, MbArtist(result))
        self.finish()

def fetch_artist(artist_id, callback):
    worker = FetchArtistWorker(artist_id)
    worker.result.connect(callback)
    workers.execute(worker)


# ======= FETCH RELEASE COVER ======
# Fetch the cover of a release
# ==================================

class FetchReleaseCoverWorker(Worker):
    result = pyqtSignal(str, bytes)

    # size can be: “250”, “500”, “1200” or None.
    # If it is None, the largest available picture will be downloaded.
    def __init__(self, release_id: str, size="250"):
        super().__init__()
        self.release_id = release_id
        self.size = size

    @pyqtSlot()
    def run(self):
        try:
            debug(f"MUSICBRAINZ: get_image: '{self.release_id}'")
            image = mb.get_image(self.release_id, "front", size=self.size)
            debug(f"MUSICBRAINZ: get_image: '{self.release_id}' retrieved")
            self.result.emit(self.release_id, image)
        except mb.ResponseError:
            print(f"WARN: no image for release '{self.release_id}'")
            self.result.emit(self.release_id, bytes())
        self.finish()


def fetch_release_cover(release_id, callback):
    worker = FetchReleaseCoverWorker(release_id)
    worker.result.connect(callback)
    workers.execute(worker)
