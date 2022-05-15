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
        try:
            self.year: str = mb_release_group["first-release-date"].split("-")[0]
        except:
            self.year = "Unknown"
        self.score: int = int(mb_release_group.get("ext-score", 0))
        self.artists = []
        self.releases = []
        if "artist-credit" in mb_release_group:
            self.artists = [{
                "id": artist_credit["artist"]["id"],
                "name": artist_credit["artist"]["name"],
            }  for artist_credit in mb_release_group["artist-credit"] if isinstance(artist_credit, dict)]
        if "release-list" in mb_release_group:
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

class MbArtist:
    def __init__(self, mb_artist):
        self.id = mb_artist["id"]
        self.name = mb_artist["name"]
        self.release_groups = []
        if "release-group-list" in mb_artist:
            self.release_groups = [
                MbReleaseGroup(release_group) for release_group in mb_artist["release-group-list"]
            ]