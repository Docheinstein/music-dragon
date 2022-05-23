
# ======= FETCH YOUTUBE TRACKS RUNNABLE ===============
# Fetch the youtube videos associated with the tracks
# =====================================================
from difflib import get_close_matches
from typing import Optional

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from ytmusicapi import YTMusic

import workers
from log import debug
from utils import j, Mergeable
from workers import Worker

_yt: Optional[YTMusic] = None

def initialize(auth_file):
    global _yt
    _yt = YTMusic(auth_file)


def ytmusic_video_id_to_url(video_id: str):
    return f"https://music.youtube.com/watch?v={video_id}"

def ytmusic_video_url_to_id(video_url: str):
    return video_url.split("=")[-1]

class YtTrack(Mergeable):
    def __init__(self, yt_track: dict):
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

def search_youtube_track(query: str, callback, priority=workers.WorkerScheduler.PRIORITY_NORMAL):
    worker = SearchYoutubeTrackWorker(query)
    worker.result.connect(callback)
    workers.schedule(worker, priority=priority)

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

        closest_artist_names = get_close_matches(artist_query, [artist["artist"] for artist in artists])
        debug(f"closest_artist_names={closest_artist_names}")
        if closest_artist_names:
            closest_artist_name = closest_artist_names[0]
            debug(f"Closest artist found: {closest_artist_name}")
            artist = [a for a in artists if a["artist"] == closest_artist_name][0]

            debug(f"YOUTUBE_MUSIC: get_artist(artist='{artist['browseId']}')")
            artist_details = _yt.get_artist(artist["browseId"])

            debug(
                "=== yt_get_artist ==="
                f"{j(artist_details)}"
                "======================"
            )

            if "albums" in artist_details:
                if "params" in artist_details["albums"]:

                    debug(f"YOUTUBE_MUSIC: get_artist_albums(artist='{artist['browseId']}')")
                    artist_albums = _yt.get_artist_albums(artist["browseId"], artist_details["albums"]["params"])
                    debug(
                        "=== yt_get_artist ==="
                        f"{j(artist_albums)}"
                        "======================"
                    )

                    debug(j(artist_albums))

                    closest_album_names = get_close_matches(album_query, [album["title"] for album in artist_albums])
                    debug(f"closest_album_names={closest_album_names}")

                    if closest_album_names:
                        closest_album_name = closest_album_names[0]
                        debug(f"Closest album found: {closest_album_name}")
                        album = [a for a in artist_albums if a["title"] == closest_album_name][0]


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
                        emission = [YtTrack(yttrack) for yttrack in result]
                else:
                    print("WARN: no 'params' key for artist albums")
            else:
                print(f"WARN: no album close to '{album_query}' for artist '{artist_query}'")
        else:
            print(f"WARN: no artist close to '{artist_query}'")

        self.result.emit(self.artist_name, self.album_title, emission)


def search_youtube_album_tracks(artist_name: str, album_title: str, callback, priority=workers.WorkerScheduler.PRIORITY_NORMAL):
    worker = SearchYoutubeAlbumTracksWorker(artist_name, album_title)
    worker.result.connect(callback)
    workers.schedule(worker, priority=priority)


