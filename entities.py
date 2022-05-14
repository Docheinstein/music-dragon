# ====== ENTITIES =======

from typing import Optional

from cache import COVER_CACHE


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

class MbTrack:
    def __init__(self, mb_release: 'MbRelease', mb_track):
        self.id = mb_track["recording"]["id"]
        self.length = int(mb_track["recording"]["length"]) if "length" in mb_track["recording"] else 0
        self.title = mb_track["recording"]["title"]
        self.track_number = mb_track["position"]
        self.release = mb_release
        self.youtube_track: Optional[YtTrack] = None


class MbRelease:
    def __init__(self, mb_release_group: 'MbReleaseGroup', mb_release):
        self.release_group = mb_release_group
        self.id: str = mb_release["id"]
        self.title: str = mb_release["title"]
        self.tracks = [MbTrack(self, track) for track in mb_release["medium-list"][0]["track-list"]]

class MbReleaseGroup:
    def __init__(self, mb_release_group):
        self.id: str = mb_release_group["id"]
        self.title: str = mb_release_group["title"]
        self.score: int = int(mb_release_group.get("ext-score", 0))
        self.artists = [{
            "id": artist_credit["artist"]["id"],
            "name": artist_credit["artist"]["name"],
        }  for artist_credit in mb_release_group["artist-credit"] if isinstance(artist_credit, dict)]
        self.releases = [{
            "id": release["id"],
            "title": release["title"],
        }  for release in mb_release_group["release-list"]]

    def artists_string(self):
        if not self.artists:
            return "Unknown Artist"
        return ", ".join(artist["name"] for artist in self.artists)

    def cover(self):
        return COVER_CACHE.get(self.id)
