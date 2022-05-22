from difflib import get_close_matches
from statistics import mean
from typing import List, Dict, Optional

import musicbrainz
import preferences
import wiki
import ytdownloader
import ytmusic
from ytmusic import YtTrack
from log import debug
from musicbrainz import MbArtist, MbReleaseGroup, MbRelease, MbTrack
from utils import j, Mergeable

_artists: Dict[str, 'Artist'] = {}
_release_groups: Dict[str, 'ReleaseGroup'] = {}
_releases: Dict[str, 'Release'] = {}
_tracks: Dict[str, 'Track'] = {}
_youtube_tracks: Dict[str, 'YtTrack'] = {}

class Images:
    def __init__(self):
        self.images = {}
        self.preferred_image_id = None

    def set_image(self, image_id, image, preferred=None):
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
        debug(f"set_image: images now are {self}")

    def get_image(self, image_id):
        return self.images.get(image_id)

    def preferred_image(self):
        return self.images.get(self.preferred_image_id)

    def preferred_image_index(self):
        try:
            return list(self.images.keys()).index(self.preferred_image_id)
        except ValueError:
            return None

    def set_preferred_image_next(self):
        debug("set_preferred_image_next")
        try:
            keys = list(self.images.keys())
            preferred_image_idx = keys.index(self.preferred_image_id)
            next_preferred_image_idx = (preferred_image_idx + 1) % len(keys)
            debug(f"set_preferred_image_next: old is {self.preferred_image_id} (at index {preferred_image_idx})")
            self.preferred_image_id = keys[next_preferred_image_idx]
            debug(f"set_preferred_image_next: new is {self.preferred_image_id} (at index {next_preferred_image_idx})")
        except ValueError:
            pass

    def count(self):
        return len(self.images)

    def better(self, other: 'Images'):
        return len(self.images.keys()) > len(other.images.keys())

    def __str__(self):
        return ", ".join([f'(key={key}, size={int(len(img) / 1024)}KB, preferred={self.preferred_image_id == key})' for key, img in self.images.items()])

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

    def main_release(self):
        return get_release(self.main_release_id)

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

        self.front_cover = None
        self.fetched_front_cover = False
        self.fetched_youtube_video_ids = False

    def merge(self, other):
        # handle flags apart
        fetched_front_cover = self.fetched_front_cover or other.fetched_front_cover
        fetched_youtube_video_ids = self.fetched_youtube_video_ids or other.fetched_youtube_video_ids
        super().merge(other)
        self.fetched_front_cover = fetched_front_cover
        self.fetched_youtube_video_ids = fetched_youtube_video_ids

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
        self.track_number = mb_track.track_number
        self.release_id = mb_track.release_id
        self.youtube_track_id = None
        self.fetched_youtube_track = False
        self.youtube_track_is_official = False

    def merge(self, other):
        # TODO: youtube_track_is_official is not handled well probably
        # handle flags apart
        fetched_youtube_track = self.fetched_youtube_track or other.fetched_youtube_track
        super().merge(other)
        self.fetched_youtube_track = fetched_youtube_track

    def release(self):
        return get_release(self.release_id)

    def youtube_track(self):
        return get_youtube_track(self.youtube_track_id)

def _add_artist(artist: Artist):
    debug(f"add_artist({artist.id})")

    if  artist.id not in _artists:
        _artists[artist.id] = artist
    else:
        _artists[artist.id].merge(artist)
    return get_artist(artist.id)

def _add_release_group(release_group: ReleaseGroup):
    debug(f"add_release_group({release_group.id})")
    if  release_group.id not in _release_groups:
        _release_groups[release_group.id] = release_group
    else:
        _release_groups[release_group.id].merge(release_group)
    return get_release_group(release_group.id)

def _add_release(release: Release):
    debug(f"add_release({release.id})")
    if release.id not in _releases:
        _releases[release.id] = release
    else:
        _releases[release.id].merge(release)
    return get_release(release.id)

def _add_track(track: Track):
    debug(f"add_track({track.id})")
    if track.id not in _tracks:
        _tracks[track.id] = track
    else:
        _tracks[track.id].merge(track)
    return get_track(track.id)

def _add_youtube_track(yttrack: YtTrack):
    debug(f"add_youtube_track({yttrack.id})")
    if yttrack.id not in _youtube_tracks:
        _youtube_tracks[yttrack.id] = yttrack
    else:
        _youtube_tracks[yttrack.id].merge(yttrack)
    return get_youtube_track(yttrack.id)

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

def get_youtube_track(youtube_track_id) -> Optional[YtTrack]:
    res = _youtube_tracks.get(youtube_track_id)
    if res:
        debug(f"get_youtube_track({youtube_track_id}): found")
    else:
        debug(f"get_youtube_track({youtube_track_id}): not found")
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
        release_group_cover_callback(release_group_id, rg.images.get_image(release_group_id))
    else:
        # actually fetch
        debug(f"Release group ({release_group_id}) cover not fetched yet")
        def release_group_cover_callback_wrapper(rg_id, image):
            _release_groups[rg_id].fetched_front_cover = True
            if image:
                _release_groups[rg_id].images.set_image(rg_id, image)
            release_group_cover_callback(rg_id, image)

        musicbrainz.fetch_release_group_cover(release_group_id, preferences.cover_size(), release_group_cover_callback_wrapper)

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
                    _artists[artist_id__].fetched_image = True
                    if image:
                        _artists[artist_id__].images.set_image(artist_id__, image)
                    artist_image_callback(artist_id_, image)

                if "wikidata" in result.urls:
                    wiki_id = result.urls["wikidata"].split("/")[-1]
                    wiki.fetch_wikidata_image(wiki_id, artist_image_callback_wrapper, user_data=artist_id)

        musicbrainz.fetch_artist(artist_id, artist_callback_wrapper)


def fetch_release_cover(release_id: str, release_cover_callback):
    debug(f"fetch_release_cover(release_id={release_id})")

    r = get_release(release_id)
    if r and r.fetched_front_cover:
        # cached
        debug(f"Release ({release_id}) cover already fetched, calling release_cover_callback directly")
        release_cover_callback(release_id, r.front_cover)
    else:
        # actually fetch
        debug(f"Release ({release_id}) cover not fetched yet")
        def release_cover_callback_wrapper(r_id, image):
            release = _releases[r_id]
            release.front_cover = image
            release.fetched_front_cover = True
            if image:
                release.release_group().images.set_image(r_id, image)
            release_cover_callback(r_id, image)

        musicbrainz.fetch_release_cover(release_id, preferences.cover_size(), release_cover_callback_wrapper)


def search_release_youtube_tracks(release_id: str, release_youtube_tracks_callback):
    debug(f"search_release_youtube_tracks(release_id={release_id})")

    r = get_release(release_id)
    rg = r.release_group()
    if r and r.fetched_youtube_video_ids:
        # cached
        release_youtube_tracks_callback(release_id, [t.youtube_track() for t in r.tracks()])
    else:
        # actually fetch
        def release_youtube_tracks_callback_wrapper(artist_name, album_title, yttracks: List[YtTrack]):
            release = _releases[release_id]
            tracks = release.tracks()
            track_names = [t.title for t in tracks]
            release.fetched_youtube_video_ids = True

            for yttrack_ in yttracks:
                yttrack = _add_youtube_track(yttrack_)

                debug(f"Handling yttrack: {yttrack.video_title}")

                closest_track_names = get_close_matches(yttrack.video_title, track_names)
                debug(f"closest_track_names={closest_track_names}")
                if closest_track_names:
                    closest_track_name = closest_track_names[0]
                    debug(f"Closest track found: {closest_track_name}")
                    closest_track_index = track_names.index(closest_track_name)
                    closest_track = tracks[closest_track_index]
                    closest_track.fetched_youtube_track = True
                    closest_track.youtube_track_is_official = True
                    closest_track.youtube_track_id = yttrack.id
                else:
                    print(f"WARN: no close track found for youtube track with title {yttrack.video_title}")

            release_youtube_tracks_callback(release_id, yttracks)

        ytmusic.search_youtube_album_tracks(rg.artists_string(), rg.title, release_youtube_tracks_callback_wrapper)

def search_track_youtube_track(track_id: str, track_youtube_track_callback):
    debug(f"search_track_youtube_track(track_id={track_id})")

    t = get_track(track_id)
    if t and t.fetched_youtube_track:
        # cached
        track_youtube_track_callback(track_id, t.youtube_track())
    else:
        # actually fetch
        def track_youtube_track_callback_wrapper(query, yttrack: YtTrack):
            _add_youtube_track(yttrack)

            track_ = _tracks[track_id]
            track_.fetched_youtube_track = True
            track_.youtube_track_id = yttrack.id
            track_youtube_track_callback(track_id, yttrack)

        query = t.release().release_group().artists_string() + " " + t.title
        ytmusic.search_youtube_track(query, track_youtube_track_callback_wrapper)


def download_youtube_track(track_id: str, started_callback, progress_callback, finished_callback):
    track = get_track(track_id)
    rg = track.release().release_group()

    if not track.youtube_track_id:
        print(f"WARN: not youtube track associated with track {track.id}")
        return

    def started_callback_wrapper(video_id: str, track_id_: str):
        started_callback(track_id)

    def progress_callback_wrapper(video_id: str, progress: float, track_id_: str):
        progress_callback(track_id, progress)

    def finished_callback_wrapper(video_id: str, track_id_: str):
        finished_callback(track_id)

    ytdownloader.start_track_download(
        video_id=track.youtube_track().video_id,
        artist=rg.artists_string(),
        album=rg.title,
        song=track.title,
        track_num=track.track_number,
        image=rg.images.preferred_image(),
        output_directory=preferences.directory(),
        output_format=preferences.output_format(),
        started_callback=started_callback_wrapper,
        progress_callback=progress_callback_wrapper,
        finished_callback=finished_callback_wrapper,
        apply_tags=True,
        user_data=track.id
    )