import musicbrainzngs as mb
from PyQt5.QtCore import pyqtSignal

from music_dragon import workers, APP_DISPLAY_NAME, APP_VERSION
from music_dragon.log import debug
from music_dragon.utils import j
from music_dragon.workers import Worker
from musicbrainzngs import musicbrainz

def initialize():
    mb.set_useragent(APP_DISPLAY_NAME, APP_VERSION)

def release_belongs_to_official_album(mb_release: dict):
    # return mb_release.get("status", "").lower() == "official" and \
    return "release-group" in mb_release and release_group_is_official_album(mb_release["release-group"])

def release_group_is_official_album(mb_release_group: dict):
    return "primary-type" in mb_release_group and mb_release_group.get("primary-type") in ["Album", "EP"] \
           and ("secondary-type-list" not in mb_release_group or not mb_release_group["secondary-type-list"] or
                (len(mb_release_group["secondary-type-list"]) == 1 and
                 mb_release_group["secondary-type-list"][0] in ["Soundtrack"]))

#
# class MbTrack: # recording belonging to a release
#     def __init__(self, mb_track=None, release_id=None):
#         self.id = None
#         self.title = None
#         self.length = 0
#         self.track_number = None
#         self.release_id = None
#         if mb_track:
#             self.id = f'{mb_track["recording"]["id"]}@{release_id}' # unique within release
#             self.title = mb_track["recording"]["title"]
#             self.length = int(mb_track["recording"].get("length", 0))
#             self.track_number = int(mb_track["position"])
#             self.release_id = release_id
#
#
#
# class MbRecording: # recording (possibly belongs to multiple releases)
#     def __init__(self, mb_recording=None):
#         self.id = None
#         self.title = None
#         self.length = 0
#         self.artists = []
#         self.releases = []
#
#         if mb_recording:
#             self.id = mb_recording["id"]
#             self.title = mb_recording["title"]
#             self.length = int(mb_recording.get("length", 0))
#
#
#             if "artist-credit" in mb_recording:
#                 self.artists = [{
#                     "id": artist_credit["artist"]["id"],
#                     "name": artist_credit["artist"]["name"],
#                     "aliases": [alias["alias"] for alias in artist_credit["artist"].get("aliases-list", [])]
#                 }  for artist_credit in mb_recording["artist-credit"] if isinstance(artist_credit, dict)]
#
#             if "release-list" in mb_recording:
#                 rg_ids = set()
#                 for r in mb_recording["release-list"]:
#                     if _release_belongs_to_official_album(r):
#                         rg_id = r["release-group"]["id"]
#                         if rg_id not in rg_ids:
#                             # take only release belonging to a release group not added yet
#                             rg_ids.add(rg_id)
#                             self.releases.append(
#                                 {
#                                     "id": r["id"],
#                                     "title": r["title"],
#                                     "release-group": {
#                                         "id": r["release-group"]["id"],
#                                         "title": r["release-group"]["title"]
#                                     }
#                                 }
#                             )
#
#
# class MbRelease:
#     def __init__(self, mb_release=None):
#         self.id = None
#         self.title = None
#         self.format = None
#         self.release_group_id = None
#         self.tracks = []
#         if mb_release:
#             self.id: str = mb_release["id"]
#             self.title: str = mb_release["title"]
#             self.format = mb_release["medium-list"][0]["format"] if "format" in mb_release["medium-list"][0] else None
#             self.release_group_id = mb_release["release-group"]["id"]
#             self.tracks = [MbTrack(track, mb_release["id"]) for track in mb_release["medium-list"][0]["track-list"]]
#
# class MbReleaseGroup:
#     def __init__(self, mb_release_group=None):
#         self.id = None
#         self.title = None
#         self.date = None
#         self.score = None
#
#         self.artists = []
#         self.releases = []
#
#         if mb_release_group:
#             self.id: str = mb_release_group["id"]
#             self.title: str = mb_release_group["title"]
#             self.date = mb_release_group.get("first-release-date", "9999-99-99")
#             self.score: int = int(mb_release_group.get("ext-score", 0))
#
#
#             if "artist-credit" in mb_release_group:
#                 self.artists = [{
#                     "id": artist_credit["artist"]["id"],
#                     "name": artist_credit["artist"]["name"],
#                     "aliases": [alias["alias"] for alias in artist_credit["artist"].get("aliases-list", [])]
#                 }  for artist_credit in mb_release_group["artist-credit"] if isinstance(artist_credit, dict)]
#             if "release-list" in mb_release_group:
#                 self.releases = [{
#                     "id": release["id"],
#                     "title": release["title"],
#                 }  for release in mb_release_group["release-list"]]
#
# class MbArtist:
#     def __init__(self, mb_artist=None):
#         self.id = None
#         self.name = None
#         self.aliases = []
#         self.release_groups = []
#         self.urls = {}
#
#         if mb_artist:
#             self.id = mb_artist["id"]
#             self.name = mb_artist["name"]
#
#             if "aliases-list" in mb_artist:
#                 self.aliases = [alias["alias"] for alias in mb_artist["aliases-list"]]
#
#             if "release-group-list" in mb_artist:
#                 for release_group in mb_artist["release-group-list"]:
#                     if not _release_group_is_official_album(release_group):
#                         debug(f"Skipping release group: {release_group['title']}")
#                         continue
#
#                     mb_release_group = MbReleaseGroup(release_group)
#
#                     # TODO: what if there is more than an artist?
#                     mb_release_group.artists.append({
#                         "id": self.id,
#                         "name": self.name,
#                         "aliases": self.aliases
#                     })
#                     self.release_groups.append(mb_release_group)
#                 # sort release groups by date
#                 self.release_groups.sort(key=lambda mbrg: mbrg.date)
#
#             if "url-relation-list" in mb_artist:
#                 for url in mb_artist["url-relation-list"]:
#                     self.urls[url["type"]] = url["target"]
#


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

        # artists = [MbArtist(a) for a in result]

        self.result.emit(self.query, result)

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
            # self.query, limit=self.limit, primarytype="Album"
        )["release-group-list"]
        debug(
            "=== search_release_groups ==="
            f"{j(result)}"
            "======================"
        )
        # release_groups = [MbReleaseGroup(release_group) for release_group in result
        #                   if _release_group_is_official_album(release_group)]
        release_groups = [release_group for release_group in result
                          if release_group_is_official_album(release_group)]
        self.result.emit(self.query, release_groups)

def search_release_groups(query, callback, limit, priority=workers.Worker.PRIORITY_NORMAL):
    worker = SearchReleaseGroupsWorker(query, limit)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)


# ========== SEARCH RECORDINGS ==========
# Search recordings for a given query
# =======================================

class SearchRecordingsWorker(Worker):
    result = pyqtSignal(str, str, list)

    def __init__(self, recording_query, artist_hint, limit):
        super().__init__()
        self.recording_query = recording_query
        self.artist_hint = artist_hint
        self.limit = limit

    def run(self):
        if not self.recording_query:
            return

        if self.artist_hint:
            debug(f"MUSICBRAINZ: search_recordings: recording='{self.recording_query}', artist='{self.artist_hint}'")
            result = mb.search_recordings(
                self.recording_query, artistname=self.artist_hint, primarytype="Album", limit=self.limit, strict=True
            )["recording-list"]
        else:
            debug(f"MUSICBRAINZ: search_recordings: '{self.recording_query}'")
            result = mb.search_recordings(
                self.recording_query, primarytype="Album", limit=self.limit
            )["recording-list"]

        debug(
            "=== search_recordings ==="
            f"{j(result)}"
            "======================"
        )

        # strip out non-official releases
        for t in result:
            if "release-list" not in t:
                t["release-list"] = []
            t["release-list"] = [rel for rel in t["release-list"] if release_belongs_to_official_album(rel)]

        self.result.emit(self.recording_query, self.artist_hint or "", result)

def search_recordings(recording_query, artist_hint, callback, limit, priority=workers.Worker.PRIORITY_NORMAL):
    worker = SearchRecordingsWorker(recording_query, artist_hint, limit)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)


# ========== SEARCH RELEASE GROUP ==========
# Search release group for a given query
# =======================================

class SearchReleaseGroupWorker(Worker):
    result = pyqtSignal(str, str, list)

    def __init__(self, artist, album):
        super().__init__()
        self.artist = artist
        self.album = album

    def run(self):
        debug(f"MUSICBRAINZ: search_release_groups: artist='{self.artist}', album='{self.album}'")
        result = mb.search_release_groups(
            self.album, artistname=self.artist, primarytype="Album", strict=True
        )["release-group-list"]

        debug(
            "=== search_release_groups ==="
            f"{j(result)}"
            "======================"
        )

        # strip out non-official releases
        release_groups = [release_group for release_group in result
                          if release_group_is_official_album(release_group)]

        self.result.emit(self.artist, self.album, release_groups)

def search_release_group(artist, album, callback, priority=workers.Worker.PRIORITY_NORMAL):
    worker = SearchReleaseGroupWorker(artist, album)
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

        # releases = [MbRelease(release) for release in result]

        self.result.emit(self.release_group_id, result)


def fetch_release_group_releases(release_group_id, callback, priority=workers.Worker.PRIORITY_NORMAL):
    worker = FetchReleaseGroupReleasesWorker(release_group_id)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)


# ============ FETCH ARTIST =============
# Fetch the details of the given artist
# =======================================

class FetchArtistWorker(Worker):
    result = pyqtSignal(str, dict)

    def __init__(self, artist_id: str):
        super().__init__()
        self.artist_id = artist_id

    def run(self):
        # Fetch all the releases and releases tracks for the release groups
        # result = mb.get_artist_by_id(self.artist_id, includes=["aliases", "release-groups", "url-rels", "annotation", "releases", "isrcs"])
        debug(f"MUSICBRAINZ: get_artist_by_id: '{self.artist_id}'")

        # def get_artist_by_id_ext(id, includes=[], release_status=[], release_type=[], limit=25):
        #     params = musicbrainz._check_filter_and_make_params("artist", includes,
        #                                            release_status, release_type)
        #     params["limit"] = limit
        #     return musicbrainz._do_mb_query("artist", id, includes, params)

        result = mb.get_artist_by_id(
            self.artist_id,
            # includes=["aliases", "release-groups", "release-group-rels", "releases", "url-rels"],
            includes=["aliases", "release-groups", "release-group-rels", "url-rels"],
            # release_status=["official"],
            release_type=["album", "ep"],
        )["artist"]
        debug(
            "=== get_artist_by_id ==="
            f"{j(result)}"
            "======================"
        )

        release_group_list = result["release-group-list"]
        release_group_count = result["release-group-count"]

        if len(release_group_list) < release_group_count:
            debug("Too many release groups, browsing them...")

            release_group_list = []
            while len(release_group_list) < release_group_count:
                offset = len(release_group_list)
                # debug(f"browse_release_groups(artist={self.artist_id},offset={offset},limit={25}) [COUNT is {release_group_count}]")
                # rgs_result = browse_release_groups(artist=self.artist_id,
                #                         includes=["release-rels", "release-group-rels"],
                #                         release_type=["album"],
                #                         limit=25,
                #                         offset=offset)
                debug(f"search_release_groups(artist={self.artist_id},offset={offset},limit={25}) [COUNT is {release_group_count}]")

                rgs_result = mb.search_release_groups(
                    query="",
                    limit=100,
                    offset=offset,
                    strict=True,
                    arid=self.artist_id,
                    primarytype="album",
                    status="official"
                )

                debug(
                    f"=== search_release_groups (offset={offset}) ==="
                    f"{j(rgs_result)}"
                    "======================"
                )

                release_group_list += rgs_result["release-group-list"]
                release_group_count = rgs_result["release-group-count"]

            release_group_list = sorted(release_group_list, key=lambda rg: rg.get("first-release-date", "9999-99-99"))
            result["release-group-list"] = release_group_list

        debug(
            "=== get_artist_by_id EXTENDED ==="
            f"{j(result)}"
            "======================"
        )


        self.result.emit(self.artist_id, result)

def fetch_artist(artist_id, callback, priority=workers.Worker.PRIORITY_NORMAL):
    worker = FetchArtistWorker(artist_id)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)


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
