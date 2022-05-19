from statistics import mean
from typing import List, Dict, Optional

import musicbrainz
import wiki
from log import debug
from musicbrainz import MbArtist, MbReleaseGroup, MbRelease, MbTrack

_artists: Dict[str, 'Artist'] = {}
_release_groups: Dict[str, 'ReleaseGroup'] = {}
_releases: Dict[str, 'Release'] = {}
_tracks: Dict[str, 'Track'] = {}

class Images:
    def __init__(self):
        self.images = {}
        self.preferred_image_id = None

    def set_image(self, image, image_id="default", preferred=None):
        self.images[image_id] = image
        if preferred is True:
            # True: always override
            self.preferred_image_id = image_id
        elif preferred is None and self.preferred_image_id is None:
            # None: override only if there is no preferred image yet
            self.preferred_image_id = image_id
        else:
            # False: don't override
            pass
        debug(f"set_image: images now are {[f'{key}:{int(len(img) / 1024)}KB' for key, img in self.images.items()]}")

    def get_image(self, image_id="default"):
        return self.images.get(image_id)

    def preferred_image(self):
        return self.images.get(self.preferred_image_id)

    def better(self, other: 'Images'):
        return len(self.images.keys()) > len(other.images.keys())

class Mergeable:
    def merge(self, other):
        debug("===== merging =====\n"
              f"{(vars(self))}\n"
              "------ with -----\n"
              f"{(vars(other))}\n"
        )
        # TODO: recursive check of better()? evaluate len() if hasattr(len) eventually?

        # object overriding better
        if hasattr(self, "better") and hasattr(other, "better"):
            if other.better(self):
                for attr, value in vars(self).items():
                    if hasattr(other, attr):
                        self.__setattr__(attr, other.__getattribute__(attr))
        else:
            # default case
            for attr, value in vars(self).items():
                if attr.startswith("_"):
                    continue # skip private attributes
                if hasattr(other, attr):
                    other_value = other.__getattribute__(attr)
                    # nested object overriding better()
                    if hasattr(value, "better") and hasattr(other_value, "better") and other_value.better(value):
                        self.__setattr__(attr, other_value)
                    # default case
                    else:
                        self.__setattr__(attr, value or other_value)

class Artist(Mergeable):
    def __init__(self, mb_artist: MbArtist):
        self.id = mb_artist.id
        self.name = mb_artist.name
        self.aliases = mb_artist.aliases
        self.images = Images()
        self.release_group_ids = [rg.id for rg in mb_artist.release_groups]

        for release_group in mb_artist.release_groups:
            _add_release_group(ReleaseGroup(release_group))

        self.fetched = False
        self.fetched_image = False

    def merge(self, other):
        # handle flags apart
        fetched = self.fetched or other.fetched
        fetched_image = self.fetched_image or other.fetched_image
        super().merge(other)
        self.fetched = fetched
        self.fetched_image = fetched_image

    def release_groups(self):
        return [get_release_group(rg) for rg in self.release_group_ids]

    def release_group_count(self):
        return len(self.release_group_ids)

class ReleaseGroup(Mergeable):
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

        self.fetched_releases = False
        self.fetched_front_cover = False

    def merge(self, other):
        # handle flags apart
        fetched_releases = self.fetched_releases or other.fetched_releases
        fetched_front_cover = self.fetched_front_cover or other.fetched_front_cover
        super().merge(other)
        self.fetched_releases = fetched_releases
        self.fetched_front_cover = fetched_front_cover

    def artists(self):
        return [get_artist(a) for a in self.artist_ids]

    def artists_string(self):
        artists = self.artists()
        if not artists or artists.count(None):
            return "Unknown Artist"
        return ", ".join(a.name for a in artists)

    def releases(self):
        return [get_release(r) for r in self.release_ids]

    def year(self):
        try:
            return self.date.split("-")[0]
        except:
            return self.date

class Release(Mergeable):
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

class Track(Mergeable):
    def __init__(self, mb_track: MbTrack):
        self.id = mb_track.id
        self.title = mb_track.title
        self.release_id = mb_track.release_id

    def release(self):
        return get_release(self.release_id)

def _add_artist(artist: Artist):
    debug(f"add_artist({artist.id})")

    if  artist.id not in _artists:
        _artists[artist.id] = artist
    else:
        _artists[artist.id].merge(artist)

def _add_release_group(release_group: ReleaseGroup):
    debug(f"add_release_group({release_group.id})")
    if  release_group.id not in _release_groups:
        _release_groups[release_group.id] = release_group
    else:
        _release_groups[release_group.id].merge(release_group)

def _add_release(release: Release):
    debug(f"add_release({release.id})")
    if release.id not in _releases:
        _releases[release.id] = release
    else:
        _releases[release.id].merge(release)

def _add_track(track: Track):
    debug(f"add_release({track.id})")
    if track.id not in _tracks:
        _tracks[track.id] = track
    else:
        _tracks[track.id].merge(track)

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
    debug(f"search_artists(query={query})")
    def artists_callback_wrapper(query_, result: List[MbArtist]):
        artists = [Artist(a) for a in result]
        for a in artists:
            _add_artist(a)
        artists_callback(query_, artists)

        # (eventually) image
        if artist_image_callback:
            def artist_callback(_1, _2):
                pass

            for a in result:
                fetch_artist(a.id, artist_callback, artist_image_callback)

    musicbrainz.search_artists(query, artists_callback_wrapper, limit)

def search_release_groups(query, release_groups_callback, release_group_image_callback=None, limit=3):
    debug(f"search_release_groups(query={query})")

    def release_groups_callback_wrapper(query_, result: List[MbReleaseGroup]):
        release_groups = [ReleaseGroup(rg) for rg in result]
        for rg in release_groups:
            _add_release_group(rg)
        release_groups_callback(query_, release_groups)

        # (eventually) image
        if release_group_image_callback:
            for rg in result:
                fetch_release_group_cover(rg.id, release_group_image_callback)

    musicbrainz.search_release_groups(query, release_groups_callback_wrapper, limit)

def fetch_release_group_cover(release_group_id: str, release_group_cover_callback):
    debug(f"fetch_release_group_cover(release_group_id={release_group_id})")

    rg = get_release_group(release_group_id)
    if rg and rg.fetched_front_cover:
        # cached
        debug(f"Release group ({release_group_id}) cover already fetched, calling release_group_cover_callback directly")
        release_group_cover_callback(release_group_id, rg.images.get_image(image_id="release_group_front_cover"))
    else:
        # actually fetch
        debug(f"Release group ({release_group_id}) cover not fetched yet")
        def release_group_cover_callback_wrapper(rg_id, image):
            _release_groups[rg_id].images.set_image(image, image_id="release_group_front_cover")
            _release_groups[rg_id].fetched_front_cover = True
            release_group_cover_callback(rg_id, image)

        musicbrainz.fetch_release_group_cover(release_group_id, release_group_cover_callback_wrapper)

def fetch_release_group_releases(release_group_id: str, release_group_releases_callback):
    debug(f"fetch_release_group_releases(release_group_id={release_group_id})")

    rg = get_release_group(release_group_id)
    if rg and rg.fetched_releases:
        # cached
        debug(f"Release group ({release_group_id}) releases already fetched, calling release_group_releases_callback directly")
        release_group_releases_callback(release_group_id, rg.releases())
    else:
        # actually fetch
        debug(f"Release group ({release_group_id}) releases not fetched yet")
        def release_group_releases_callback_wrapper(release_group_id_, result: List[MbRelease]):
            releases = [Release(r) for r in result]
            for r in releases:
                _add_release(r)

            # add releases to release group to
            release_group = get_release_group(release_group_id_)
            if release_group:
                release_group.release_ids = [r.id for r in releases]
                release_group.fetched_releases = True

                # Try to figure out which is the more appropriate (main) release
                # with heuristics:
                # 1. Take the release with the number of track which is more near
                #    to the average number of tracks of the releases
                avg_track_count = mean([r.track_count() for r in releases])
                deltas = [abs(r.track_count() - avg_track_count) for r in releases]
                main_release_id = releases[deltas.index(min(deltas))].id
                release_group.main_release_id = main_release_id

            release_group_releases_callback(release_group_id_, releases)

        musicbrainz.fetch_release_group_releases(release_group_id, release_group_releases_callback_wrapper)

def fetch_artist(artist_id, artist_callback, artist_image_callback=None):
    debug(f"fetch_artist(artist_id={artist_id})")

    # cached
    a = get_artist(artist_id)
    if a:
        if a.fetched:
            debug("Artist already fetched, calling artist_callback directly")
            artist_callback(artist_id, a)
        else:
            debug("Artist not fetched yet")
        if artist_image_callback and a.fetched_image:
            debug("Artist image already fetched, calling artist_image_callback directly")
            artist_image_callback(artist_id, a.images.preferred_image())
        else:
            debug("Artist image not fetched yet")

    # actually fetch
    if not a or (not a.fetched) or (not a.fetched_image):
        def artist_callback_wrapper(artist_id_, result: MbArtist):
            artist = Artist(result)
            artist.fetched = True
            _add_artist(artist)
            artist_callback(artist_id_, artist)

            if artist_image_callback:
                debug("Retrieving image too")

                def artist_image_callback_wrapper(wiki_id_, image, artist_id__):
                    _artists[artist_id__].images.set_image(image, "wikidata")
                    _artists[artist_id__].fetched_image = True
                    artist_image_callback(artist_id_, image)

                if "wikidata" in result.urls:
                    wiki_id = result.urls["wikidata"].split("/")[-1]
                    wiki.fetch_wikidata_image(wiki_id, artist_image_callback_wrapper, user_data=artist_id)

        musicbrainz.fetch_artist(artist_id, artist_callback_wrapper)
