from difflib import get_close_matches
from pathlib import Path

import Levenshtein as levenshtein
from typing import Optional, List

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QStandardPaths
from ytmusicapi import YTMusic

import workers
from log import debug
from utils import j, Mergeable, max_index, max_indexes, app_config_path
from workers import Worker

_yt: Optional[YTMusic] = None

def initialize():
    global _yt
    _yt = YTMusic()


class YtTrack(Mergeable):
    def __init__(self, yt_track: dict, track_number=None):
        self.id = yt_track["videoId"]
        self.video_id = yt_track["videoId"]
        self.video_title = yt_track["title"]
        self.album = {
            "id": yt_track["album"]["id"],
            "title": yt_track["album"]["name"]
        }
        self.artists = [{
            "id": a["id"],
            "name": a["name"]
        } for a in yt_track["artists"]]
        self.track_number = track_number

# ========== SEARCH YOUTUBE TRACK ===========
# Search youtube track for a given query
# ===========================================

class SearchYoutubeTrackWorker(Worker):
    result = pyqtSignal(str, YtTrack)

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
            self.result.emit(self.query, YtTrack(result[0]))

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
    result = pyqtSignal(str, str, list)

    def __init__(self, artist_name: str, album_title: str):
        super().__init__()
        self.artist_name = artist_name
        self.album_title = album_title

    def run(self) -> None:
        def get_closest(query, elements: List[dict], field: str) -> Optional[dict]:
            scores = [0] * len(elements)

            # Figure out the best match based on
            # 1. The query contains the target or the target contains the query
            # 2. Edit distance
            for i, e in enumerate(elements):
                e_name = e[field]
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


        emission = []

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

                    result = album_details["tracks"]
                    for yttrack in result:

                        # hack
                        yttrack["album"] = {
                            "id": album['browseId'],
                            "name": album["title"]
                        }
                    emission = [YtTrack(yttrack, track_number=num + 1) for num, yttrack in enumerate(result)]
            else:
                print(f"WARN: no album close to '{album_query}' for artist '{artist_query}'")
        else:
            print(f"WARN: no artist close to '{artist_query}'")

        self.result.emit(self.artist_name, self.album_title, emission)


def search_youtube_album_tracks(artist_name: str, album_title: str, callback, priority=workers.Worker.PRIORITY_NORMAL):
    if _yt:
        worker = SearchYoutubeAlbumTracksWorker(artist_name, album_title)
        worker.priority = priority
        worker.result.connect(callback)
        workers.schedule(worker)