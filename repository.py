from statistics import mean
from typing import List, Dict, Optional

import wiki

import musicbrainz
from log import debug
from musicbrainz import MbArtist, MbReleaseGroup, MbRelease, MbTrack

_artists: Dict[str, 'Artist'] = {}
_release_groups: Dict[str, 'ReleaseGroup'] = {}
_releases: Dict[str, 'Release'] = {}
_tracks: Dict[str, 'Track'] = {}

class Images:
    def __init__(self):
        self.images = []
        self.preferred_image_index = -1

    def add_image(self, image, preferred=True):
        self.images.append(image)
        if preferred:
            self.preferred_image_index = len(self.images) - 1

    def preferred_image(self):
        return self.images[self.preferred_image_index] if 0 <= self.preferred_image_index < len(self.images) else None

class Artist:
    def __init__(self, mb_artist: MbArtist):
        self.id = mb_artist.id
        self.name = mb_artist.name
        self.aliases = mb_artist.aliases
        self.images = Images()
        self.release_group_ids = [rg.id for rg in mb_artist.release_groups]

        for release_group in mb_artist.release_groups:
            _add_release_group(ReleaseGroup(release_group))

    def release_groups(self):
        return [get_release_group(rg) for rg in self.release_group_ids]

    def release_group_count(self):
        return len(self.release_group_ids)

class ReleaseGroup:
    def __init__(self, mb_release_group: MbReleaseGroup):
        self.id = mb_release_group.id
        self.title = mb_release_group.title
        self.date = mb_release_group.date
        self.images = Images()
        self.artist_ids = [a["id"] for a in mb_release_group.artists]
        self.release_ids = []
        self.main_release_id = None

        for artist in mb_release_group.artists:
            _add_artist(Artist(MbArtist(artist)))

    def artists(self):
        return [get_artist(a) for a in self.artist_ids]

    def releases(self):
        return [get_release(r) for r in self.release_ids]

    def artists_string(self):
        artists = self.artists()
        if not artists or artists.count(None):
            return "Unknown Artist"
        return ", ".join(a.name for a in artists)

    def year(self):
        try:
            return self.date.split("-")[0]
        except:
            return self.date

class Release:
    def __init__(self, mb_release: MbRelease):
        self.id = mb_release.id
        self.title = mb_release.title
        self.release_group_id = mb_release.release_group_id
        self.track_ids = [t.id for t in mb_release.tracks]

        for mb_track in mb_release.tracks:
            _add_track(Track(mb_track))

    def release_group(self):
        return get_release_group(self.release_group_id)

    def tracks(self):
        return [get_track(t) for t in self.track_ids]

    def track_count(self):
        return len(self.track_ids)

class Track:
    def __init__(self, mb_track: MbTrack):
        self.id = mb_track.id
        self.title = mb_track.title
        self.release_id = mb_track.release_id

    def release(self):
        return get_release(self.release_id)
        #
        #
        # self.id = mb_artist["id"]
        # self.name = mb_artist["name"]
        #
        # self.aliases = []
        # if "aliases-list" in mb_artist:
        #     self.aliases = [alias["alias"] for alias in mb_artist["aliases-list"]]
        #
        # # TODO: keep only ids
        # self.release_groups = []
        # if "release-group-list" in mb_artist:
        #     self.release_groups = [
        #         MbReleaseGroup(release_group) for release_group in mb_artist["release-group-list"]
        #     ]
        #
        # self.urls = {}
        # if "url-relation-list" in mb_artist:
        #     for url in mb_artist["url-relation-list"]:
        #         self.urls[url["type"]] = url["target"]
        #
        # self.images = Images()

def _add_artist(artist: Artist, replace=False):
    debug(f"add_artist({artist.id})")
    if replace or artist.id not in _artists:
        debug(f"Actually adding artist {artist.id}")
        _artists[artist.id] = artist
    else:
        debug("Skipping artist insertion, already exists and replace is False")

def _add_release_group(release_group: ReleaseGroup, replace=False):
    debug(f"add_release_group({release_group.id})")
    if replace or release_group.id not in _release_groups:
        debug(f"Actually adding release group {release_group.id}")
        _release_groups[release_group.id] = release_group
    else:
        debug("Skipping release group insertion, already exists and replace is False")

def _add_release(release: Release, replace=False):
    debug(f"add_release({release.id})")
    if replace or release.id not in _releases:
        debug(f"Actually adding release {release.id}")
        _releases[release.id] = release
    else:
        debug("Skipping release insertion, already exists and replace is False")

def _add_track(track: Track, replace=False):
    debug(f"add_release({track.id})")
    if replace or track.id not in _tracks:
        debug(f"Actually adding track {track.id}")
        _tracks[track.id] = track
    else:
        debug("Skipping track insertion, already exists and replace is False")

def get_artist(artist_id) -> Optional[Artist]:
    res = _artists.get(artist_id)
    if res:
        debug(f"get_artist({artist_id}): found")
    else:
        debug(f"get_artist({artist_id}): not found")
    return res

def get_release_group(release_group_id) -> Optional[ReleaseGroup]:
    res = _release_groups.get(release_group_id)
    if res:
        debug(f"get_release_group({release_group_id}): found")
    else:
        debug(f"get_release_group({release_group_id}): not found")
    return res

def get_release(release_id) -> Optional[Release]:
    res = _releases.get(release_id)
    if res:
        debug(f"get_release({release_id}): found")
    else:
        debug(f"get_release({release_id}): not found")
    return res

def get_track(track_id) -> Optional[Track]:
    res = _tracks.get(track_id)
    if res:
        debug(f"get_track({track_id}): found")
    else:
        debug(f"get_track({track_id}): not found")
    return res

def get_entity(entity_id):
    if entity_id in _artists:
        debug(f"get_entity({entity_id}): found artist")
        return _artists[entity_id]
    if entity_id in _release_groups:
        debug(f"get_entity({entity_id}): found release group")
        return _release_groups[entity_id]
    if entity_id in _releases:
        debug(f"get_entity({entity_id}): found release")
        return _releases[entity_id]
    if entity_id in _tracks:
        debug(f"get_entity({entity_id}): found track")
        return _tracks[entity_id]
    debug(f"get_entity({entity_id}): not found")
    return None

def search_artists(query, artists_callback, artist_image_callback=None, limit=3):
    def artists_callback_wrapper(query_, result: List[MbArtist]):
        artists = [Artist(a) for a in result]
        for a in artists:
            _add_artist(a)
        artists_callback(query_, artists)

        # (eventually) images
        if artist_image_callback:
            def artist_callback(_1, _2):
                pass

            for a in result:
                fetch_artist(a.id, artist_callback, artist_image_callback)

    musicbrainz.search_artists(query, artists_callback_wrapper, limit)

def search_release_groups(query, release_groups_callback, release_group_image_callback=None, limit=3):
    def release_groups_callback_wrapper(query_, result: List[MbReleaseGroup]):
        release_groups = [ReleaseGroup(rg) for rg in result]
        for rg in release_groups:
            _add_release_group(rg, replace=True) # TODO: ok?
        release_groups_callback(query_, release_groups)

        if release_group_image_callback:
            for rg in result:
                fetch_release_group_cover(rg.id, release_group_image_callback)

    musicbrainz.search_release_groups(query, release_groups_callback_wrapper, limit)


        #
        # # (eventually) releases
        # if release_group_main_release_callback:
        #     def fetch_release_group_main_release_wrapper(rg_id, main_release: MbRelease):
        #         pass
        #         # _release_groups[rg_id].main_release_id = main_release.id
        #         # _releases[main_release.id] = main_release
        #         # release_group_main_release_callback(rg_id, main_release)
        #
        #     for rg in result:
        #         musicbrainz.fetch_release_group_main_release(rg.id, fetch_release_group_main_release_wrapper)
        #
        # # (eventually) images

def fetch_release_group_cover(release_group_id: str, release_group_cover_callback):
    def release_group_image_callback_wrapper(rg_id, image):
        _release_groups[rg_id].images.add_image(image)
        release_group_cover_callback(rg_id, image)

    musicbrainz.fetch_release_group_cover(release_group_id, release_group_image_callback_wrapper)

def fetch_release_group_releases(release_group_id: str, release_group_releases_callback):
    def release_group_releases_callback_wrapper(release_group_id_, result: List[MbRelease]):
        debug("release_group_releases_callback_wrapper")
        releases = [Release(r) for r in result]
        for r in releases:
            _add_release(r)

        # add releases to release group to
        release_group = get_release_group(release_group_id_)
        if release_group:
            release_group.release_ids = [r.id for r in releases]

            # Try to figure out which is the more appropriate release with heuristics:
            # 1. Take the release with the number of track which is more near
            #    to the average number of tracks of the releases
            avg_track_count = mean([r.track_count() for r in releases])
            deltas = [abs(r.track_count() - avg_track_count) for r in releases]
            main_release_id = releases[deltas.index(min(deltas))].id
            release_group.main_release_id = main_release_id

        release_group_releases_callback(release_group_id_, releases)

    musicbrainz.fetch_release_group_releases(release_group_id, release_group_releases_callback_wrapper)

def fetch_artist(artist_id, artist_callback, artist_image_callback=None):
    def artist_callback_wrapper(artist_id_, result: MbArtist):
        artist = Artist(result)
        _add_artist(artist, replace=True)
        artist_callback(artist_id_, artist)

        if artist_image_callback:
            def artist_image_callback_wrapper(wiki_id, image, artist_id__):
                _artists[artist_id__].images.add_image(image)
                artist_image_callback(artist_id_, image)

            if "wikidata" in result.urls:
                wiki_id = result.urls["wikidata"].split("/")[-1]
                wiki.fetch_wikidata_image(wiki_id, artist_image_callback_wrapper, user_data=artist_id)

    musicbrainz.fetch_artist(artist_id, artist_callback_wrapper)
