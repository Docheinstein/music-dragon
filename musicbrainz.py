import musicbrainzngs as mb
from PyQt5.QtCore import pyqtSignal

import workers
from log import debug
from utils import j
from workers import Worker


def initialize():
    mb.set_useragent("MusicDragon", "0.1")

def _release_group_is_official_album(mb_release_group):
    return "primary-type" in mb_release_group and mb_release_group.get("primary-type") in ["Album", "EP"] and \
           ("secondary-type-list" not in mb_release_group or not mb_release_group.get("secondary-type-list"))

class MbTrack:
    def __init__(self, mb_track, release_id):
        self.id = mb_track["recording"]["id"]
        self.length = int(mb_track["recording"]["length"]) if "length" in mb_track["recording"] else 0
        self.title = mb_track["recording"]["title"]
        self.track_number = mb_track["position"]
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
                if not _release_group_is_official_album(release_group):
                    debug(f"Skipping release group: {release_group['title']}")
                    continue

                mb_release_group = MbReleaseGroup(release_group)

                # TODO: what if there is more than an artist?
                mb_release_group.artists.append({
                    "id": self.id,
                    "name": self.name,
                    "aliases": self.aliases
                })
                self.release_groups.append(mb_release_group)
            # sort release groups by date
            self.release_groups.sort(key=lambda mbrg: mbrg.date)

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

def search_artists(query, callback, limit, priority=workers.Worker.PRIORITY_NORMAL):
    worker = SearchArtistsWorker(query, limit)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)


# ========== SEARCH RELEASE GROUPS ==========
# Search the release groups for a given query
# ===========================================

class SearchReleaseGroupsWorker(Worker):
    result = pyqtSignal(str, list)

    def __init__(self, query, limit):
        super().__init__()
        self.query = query
        self.limit = limit

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
                          if _release_group_is_official_album(release_group)]

        self.result.emit(self.query, release_groups)

def search_release_groups(query, callback, limit, priority=workers.Worker.PRIORITY_NORMAL):
    worker = SearchReleaseGroupsWorker(query, limit)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)


# ======= FETCH RELEASE GROUP COVER ======
# Fetch the cover of a release group
# ========================================

class FetchReleaseGroupCoverWorker(Worker):
    result = pyqtSignal(str, bytes)

    # size can be: “250”, “500”, “1200” or None.
    # If it is None, the largest available picture will be downloaded.
    def __init__(self, release_group_id: str, size=250):
        super().__init__()
        self.release_group_id = release_group_id
        self.size = str(size) if size is not None else None

    def run(self):
        try:
            debug(f"MUSICBRAINZ: get_release_group_image_front: '{self.release_group_id}'")
            image = mb.get_release_group_image_front(self.release_group_id, size=self.size)
            debug(f"MUSICBRAINZ: get_release_group_image_front: '{self.release_group_id}' retrieved")
            self.result.emit(self.release_group_id, image)
        except mb.ResponseError:
            print(f"WARN: no image for release group '{self.release_group_id}'")
            self.result.emit(self.release_group_id, bytes())


def fetch_release_group_cover(release_group_id, size, callback, priority=workers.Worker.PRIORITY_NORMAL):
    worker = FetchReleaseGroupCoverWorker(release_group_id, size)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)


# ======= FETCH RELEASE GROUP RELEASES RUNNABLE ========
# Fetch the more appropriate release of a release group
# =====================================================

class FetchReleaseGroupReleasesWorker(Worker):
    result = pyqtSignal(str, list)

    def __init__(self, release_group_id: str):
        super().__init__()
        self.release_group_id = release_group_id

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

        self.result.emit(self.release_group_id, releases)


def fetch_release_group_releases(release_group_id, callback, priority=workers.Worker.PRIORITY_NORMAL):
    worker = FetchReleaseGroupReleasesWorker(release_group_id)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)


# ============ FETCH ARTIST =============
# Fetch the details of the given artist
# =======================================

class FetchArtistWorker(Worker):
    result = pyqtSignal(str, MbArtist)

    def __init__(self, artist_id: str):
        super().__init__()
        self.artist_id = artist_id

    def run(self):
        # Fetch all the releases and releases tracks for the release groups
        # result = mb.get_artist_by_id(self.artist_id, includes=["aliases", "release-groups", "url-rels", "annotation", "releases", "isrcs"])
        debug(f"MUSICBRAINZ: get_artist_by_id: '{self.artist_id}'")
        result = mb.get_artist_by_id(
            self.artist_id,
            includes=["aliases", "release-groups", "release-group-rels", "releases", "url-rels"],
            release_status=["official"],
            release_type=["album"],
        )["artist"]
        debug(
            "=== get_artist_by_id ==="
            f"{j(result)}"
            "======================"
        )

        self.result.emit(self.artist_id, MbArtist(result))

def fetch_artist(artist_id, callback, priority=workers.Worker.PRIORITY_NORMAL):
    worker = FetchArtistWorker(artist_id)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)



# ============ FETCH ARTIST RELEASE GROUPS =============
# Fetch the release groups of the given artist
# ======================================================
#
# class FetchArtistReleaseGroupsWorker(Worker):
#     result = pyqtSignal(str, list)
#
#     def __init__(self, artist_id: str):
#         super().__init__()
#         self.artist_id = artist_id
#
#     def run(self):
#         # Fetch all the releases and releases tracks for the release groups
#         # result = mb.get_artist_by_id(self.artist_id, includes=["aliases", "release-groups", "url-rels", "annotation", "releases", "isrcs"])
#         debug(f"MUSICBRAINZ: browse_release_groups: '{self.artist_id}'")
#         result = mb.browse_release_groups(
#             self.artist_id,
#             # includes=["aliases", "release-groups", "release-group-rels", "releases", "url-rels"],
#             # release_status=["official"],
#             release_type=["album"],
#         )["release-group-list"]
#         debug(
#             "=== browser_release_groups ==="
#             f"{j(result)}"
#             "======================"
#         )
#
#         release_groups = [MbReleaseGroup(release_group) for release_group in result
#                           if "primary-type" in release_group and release_group["primary-type"] in ["Album", "EP"] and not release_group.get("secondary-type")]
#
#         self.result.emit(self.artist_id, release_groups)
#
# def fetch_artist(artist_id, callback, priority=workers.Worker.PRIORITY_NORMAL):
#     worker = FetchArtistWorker(artist_id)
#     worker.result.connect(callback)
#     workers.schedule(worker)
#


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

    def run(self):
        try:
            debug(f"MUSICBRAINZ: get_image: '{self.release_id}'")
            image = mb.get_image(self.release_id, "front", size=self.size)
            debug(f"MUSICBRAINZ: get_image: '{self.release_id}' retrieved")
            self.result.emit(self.release_id, image)
        except mb.ResponseError:
            print(f"WARN: no image for release '{self.release_id}'")
            self.result.emit(self.release_id, bytes())


def fetch_release_cover(release_id, size, callback, priority=workers.Worker.PRIORITY_NORMAL):
    worker = FetchReleaseCoverWorker(release_id, size)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)
