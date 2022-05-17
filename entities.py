# ====== ENTITIES =======

from typing import Optional

from cache import COVER_CACHE

# TODO: better short/extended concept for entities

class YtTrack:
    def __init__(self, mb_track: 'MbTrack', yt_track):
        self.mb_track = mb_track
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
