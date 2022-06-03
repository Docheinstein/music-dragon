from typing import Optional, List

import Levenshtein as levenshtein
from PyQt5.QtCore import pyqtSignal
from ytmusicapi import YTMusic

from music_dragon import workers
from music_dragon.log import debug
from music_dragon.utils import j, Mergeable, max_index
from music_dragon.workers import Worker

_yt: Optional[YTMusic] = None

def initialize():
    global _yt
    _yt = YTMusic()


class YtTrack(Mergeable):
    def __init__(self, yt_track: dict):
        self.id = yt_track.get("videoId") or yt_track.get("id")
        self.video_id = self.id
        self.video_title = yt_track.get("title")
        self.song = yt_track.get("track") or self.video_title
        self.album = {
            "id": yt_track["album"]["id"],
            "title": yt_track["album"]["name"]
        } if "album" in yt_track and isinstance(yt_track["album"], dict) else yt_track.get("album")
        self.artists = [{
            "id": a["id"],
            "name": a["name"]
        } for a in yt_track["artists"]] if "artists" in yt_track else [yt_track.get("artist")]
        self.track_number = yt_track.get("track_number")
        self.streams = []
        self.streams_fetched = False

    def merge(self, other):
        # handle flags apart
        streams_fetched = self.streams_fetched or other.streams_fetched
        super().merge(other)
        self.streams_fetched = streams_fetched

# ========== SEARCH YOUTUBE TRACK ===========
# Search youtube track for a given query
# ===========================================

class SearchYoutubeTrackWorker(Worker):
    result = pyqtSignal(str, dict)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self) -> None:
        debug(f"YOUTUBE_MUSIC: search: '{self.query}'")
        result = _yt.search(self.query, filter="songs")
        debug(
            "=== yt_search (songs) ==="
            f"{j(result)}"
            "======================"
        )
        if result:
            self.result.emit(self.query, result[0])

def search_youtube_track(query: str, callback, priority=workers.Worker.PRIORITY_NORMAL):
    if _yt:
        worker = SearchYoutubeTrackWorker(query)
        worker.priority = priority
        worker.result.connect(callback)
        workers.schedule(worker)

# =============== SEARCH YOUTUBE ALBUM TRACKS  =================
# Search youtube tracks for a given (Artist Name, Album Title)
# ==============================================================

class SearchYoutubeAlbumTracksWorker(Worker):
    result = pyqtSignal(str, str, dict)

    def __init__(self, artist_name: str, album_title: str):
        super().__init__()
        self.artist_name = artist_name
        self.album_title = album_title

    def run(self) -> None:
        def get_closest(query, elements: List[dict], field: str) -> Optional[dict]:
            query = query.lower()
            scores = [0] * len(elements)

            # Figure out the best match based on
            # 1. The query contains the target or the target contains the query
            # 2. Edit distance
            for i, e in enumerate(elements):
                e_name = e[field]
                e_name = e_name.lower()
                if query == e_name:
                    scores[i] += 2000
                elif query in e_name or e_name in query:
                    scores[i] += 1000
                scores[i] -= levenshtein.distance(query, e_name)

                debug(f"Query='{query}', Target='{e_name}', Score={scores[i]}")

            if not scores:
                return None

            return elements[max_index(scores)]

        def get_closest_artist(query, artists: List[dict]) -> Optional[dict]:
            return get_closest(query, artists, "artist")

        def get_closest_album(query, albums: List[dict]) -> Optional[dict]:
            return get_closest(query, albums, "title")

        result = {}

        artist_query = self.artist_name
        album_query = self.album_title

        debug(f"YOUTUBE_MUSIC: search(artist='{artist_query}')")
        artists = _yt.search(artist_query, filter="artists")
        debug(
            "=== yt_search (artists) ==="
            f"{j(artists)}"
            "======================"
        )
        artist = get_closest_artist(artist_query, artists)
        if artist is not None:
            debug(f"Closest artist found: {artist['artist']}")

            debug(f"YOUTUBE_MUSIC: get_artist(artist='{artist['browseId']}')")
            artist_details = _yt.get_artist(artist["browseId"])

            debug(
                "=== yt_get_artist ==="
                f"{j(artist_details)}"
                "======================"
            )

            if "albums" in artist_details:
                if "params" in artist_details["albums"]: # must be fetched
                    debug(f"YOUTUBE_MUSIC: get_artist_albums(artist='{artist['browseId']}')")
                    artist_albums = _yt.get_artist_albums(artist["browseId"], artist_details["albums"]["params"])
                    debug(
                        "=== get_artist_albums ==="
                        f"{j(artist_albums)}"
                        "======================"
                    )
                else: # already there
                    artist_albums = artist_details["albums"]["results"]

                album = get_closest_album(album_query, artist_albums)

                if album:
                    debug(f"Closest album found: {album['title']}")

                    debug(f"YOUTUBE_MUSIC: get_album(album='{album['browseId']}')")
                    album_details = _yt.get_album(album["browseId"])
                    debug(
                        "=== yt_get_album ==="
                        f"{j(album_details)}"
                        "======================"
                    )

                    result = album_details

                    for idx, yttrack in enumerate(album_details["tracks"]):
                        # hack
                        yttrack["track_number"] = idx + 1

                        yttrack["album"] = {
                            "id": album['browseId'],
                            "name": album["title"]
                        }



            else:
                print(f"WARN: no album close to '{album_query}' for artist '{artist_query}'")
        else:
            print(f"WARN: no artist close to '{artist_query}'")

        self.result.emit(self.artist_name, self.album_title, result)


def search_youtube_album(artist_name: str, album_title: str, callback, priority=workers.Worker.PRIORITY_NORMAL):
    if _yt:
        worker = SearchYoutubeAlbumTracksWorker(artist_name, album_title)
        worker.priority = priority
        worker.result.connect(callback)
        workers.schedule(worker)

# ========== FETCH YOUTUBE TRACK ===========
# Fetch youtube track
# ===========================================

class FetchYoutubeTrackWorker(Worker):
    result = pyqtSignal(str, dict)

    def __init__(self, video_id: str):
        super().__init__()
        self.video_id = video_id

    def run(self) -> None:
        debug(f"YOUTUBE_MUSIC: get_song: '{self.video_id}'")
        result = _yt.get_song(self.video_id)
        debug(
            "=== get_song ==="
            f"{j(result)}"
            "======================"
        )
        if result:
            self.result.emit(self.video_id, result)

def fetch_track_info(video_id: str, callback, priority=workers.Worker.PRIORITY_NORMAL):
    if _yt:
        worker = FetchYoutubeTrackWorker(video_id)
        worker.priority = priority
        worker.result.connect(callback)
        workers.schedule(worker)
