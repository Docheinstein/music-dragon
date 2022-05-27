from difflib import get_close_matches
from statistics import mean, mode, multimode
from typing import List, Dict, Optional

import Levenshtein as levenshtein

import localsongs
import musicbrainz
import preferences
import wiki
import workers
import ytdownloader
import ytmusic
from localsongs import Mp3
from ytmusic import YtTrack
from log import debug
from musicbrainz import MbArtist, MbReleaseGroup, MbRelease, MbTrack, MbRecording
from utils import j, Mergeable, min_index

_artists: Dict[str, 'Artist'] = {}
_release_groups: Dict[str, 'ReleaseGroup'] = {}
_releases: Dict[str, 'Release'] = {}
_tracks: Dict[str, 'Track'] = {}
_youtube_tracks: Dict[str, 'YtTrack'] = {}

RELEASE_GROUP_IMAGES_RELEASE_GROUP_COVER_INDEX = 0
RELEASE_GROUP_IMAGES_RELEASES_FIRST_INDEX = 1
#
# class Images:
#     def __init__(self):
#         self.images = []
#         self.preferred_image_index = None

    # def set_image(self, image_id, image, preferred=None):
    #     self.images[image_id] = image
    #     if preferred is True:
    #         # True: always override
    #         self.preferred_image_id = image_id
    #     elif preferred is None and self.preferred_image_id is None:
    #         # None: override only if there is no preferred image yet
    #         self.preferred_image_id = image_id
    #     else:
    #         # False: don't override
    #         pass
    #     debug(f"set_image: images now are {self}")

    # def get_image(self, image_id):
    #     return self.images.get(image_id)
    #
    # def preferred_image(self):
    #     return self.images[self.preferred_image_index]
    #
    # def count(self):
    #     return len(self.images)
    #
    # def better(self, other: 'Images'):
    #     return len(self.images) > len(other.images)
    #
    # def __str__(self):
    #     return ", ".join([f'(idx={idx}, size={int(len(img) / 1024)}KB, preferred={self.preferred_image_index == idx})' for idx, img in enumerate(self.images)])

class Artist(Mergeable):
    def __init__(self, mb_artist: MbArtist):
        self.id = mb_artist.id
        self.name = mb_artist.name
        self.aliases = mb_artist.aliases
        # self.images = Images()
        self.image = None
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
        # self.images = Images()
        self.front_cover = None
        self.preferred_front_cover_index = 0
        self.artist_ids = [a["id"] for a in mb_release_group.artists]
        self.release_ids = []
        self.main_release_id = None

        for artist in mb_release_group.artists:
            _add_artist(Artist(MbArtist(artist)))

        self.fetched_releases = False
        self.fetched_front_cover = False

        self.fetched_youtube_video_ids = False
        self.youtube_video_ids = []

    def merge(self, other):
        # handle flags apart
        fetched_releases = self.fetched_releases or other.fetched_releases
        fetched_front_cover = self.fetched_front_cover or other.fetched_front_cover
        fetched_youtube_video_ids = self.fetched_youtube_video_ids or other.fetched_youtube_video_ids
        super().merge(other)
        self.fetched_releases = fetched_releases
        self.fetched_front_cover = fetched_front_cover
        self.fetched_youtube_video_ids = fetched_youtube_video_ids

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

    def move_preferred_front_cover_index(self, delta):
        self.preferred_front_cover_index = (self.preferred_front_cover_index + delta) % self.front_cover_count()

    def set_preferred_front_cover_release_group(self):
        self.preferred_front_cover_index = RELEASE_GROUP_IMAGES_RELEASE_GROUP_COVER_INDEX


    def set_preferred_front_cover_release(self, release_id):
        try:
            idx = self.release_ids.index(release_id)
            self.preferred_front_cover_index = RELEASE_GROUP_IMAGES_RELEASES_FIRST_INDEX + idx
        except:
            print(f"WARN: no release with id {release_id}, not chaning preferred cover")

    def preferred_front_cover(self):
        if self.preferred_front_cover_index == RELEASE_GROUP_IMAGES_RELEASE_GROUP_COVER_INDEX:
            return self.front_cover
        else:
            preferred_release_index = self.preferred_front_cover_index - RELEASE_GROUP_IMAGES_RELEASES_FIRST_INDEX
            if 0 <= preferred_release_index < len(self.release_ids):
                r = get_release(self.release_ids[preferred_release_index])
                return r.front_cover
        return None

    def front_cover_count(self):
        return len(self.release_ids) + 1

class Release(Mergeable):
    def __init__(self, mb_release: MbRelease):
        self.id = mb_release.id
        self.title = mb_release.title
        self.format = mb_release.format
        self.release_group_id = mb_release.release_group_id
        self.track_ids = [t.id for t in mb_release.tracks]


        # sanitize: avoid same title for tracks of the same album
        track_names = {}
        for mb_track in mb_release.tracks:
            t = Track(mb_track)
            if t.title not in track_names:
                track_names[t.title] = 1
            else:
                track_names[t.title] += 1
                print(f"WARN: found duplicate track title: '{t.title}', renaming it to '{t.title} ({track_names[t.title]})'")
                t.title = f"{t.title} ({track_names[t.title]})"
            _add_track(t)


        self.front_cover = None
        self.fetched_front_cover = False

    def merge(self, other):
        # handle flags apart
        fetched_front_cover = self.fetched_front_cover or other.fetched_front_cover
        super().merge(other)
        self.fetched_front_cover = fetched_front_cover

    def release_group(self):
        return get_release_group(self.release_group_id)

    def tracks(self):
        return [get_track(t) for t in self.track_ids]

    def track_count(self):
        return len(self.track_ids)

    def length(self):
        return sum([t.length for t in self.tracks()])

class Track(Mergeable):
    def __init__(self, mb_track: MbTrack):
        self.id = mb_track.id
        self.title = mb_track.title
        self.length = mb_track.length
        self.track_number = mb_track.track_number
        self.release_id = mb_track.release_id
        self.youtube_track_id = None
        self.fetched_youtube_track = False
        self.youtube_track_is_official = False
        self.downloading = False

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

    def is_available_locally(self):
        rg = self.release().release_group()
        return True if localsongs.get_by_metadata(rg.artists_string(), rg.title, self.title) else None

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

def search_tracks(query, tracks_callback, track_image_callback=None, limit=3):
    debug(f"search_tracks(query={query})")

    def recordings_callback_wrapper(query_, result: List[MbRecording]):
        # add a track for each release the recoding belongs to
        tracks = []
        for rec in result:
            for release in rec.releases:
                mb_release_group = MbReleaseGroup()
                mb_release_group.id = release["release-group"]["id"]
                mb_release_group.title = release["release-group"]["title"]
                mb_release_group.artists = [{
                    "id": a["id"],
                    "name": a["name"],
                    "aliases": [alias["alias"] for alias in a["aliases"]]
                } for a in rec.artists]

                mb_release = MbRelease()
                mb_release.id = release["id"]
                mb_release.title = release["title"]
                mb_release.release_group_id = mb_release_group.id

                mb_track = MbTrack()
                mb_track.id = f'{rec.id}@{mb_release.id}'
                mb_track.title = rec.title
                mb_track.release_id = mb_release.id

                rg = ReleaseGroup(mb_release_group)
                r = Release(mb_release)
                t = Track(mb_track)

                _add_release_group(rg)
                _add_release(r)
                _add_track(t)

                tracks.append(t)
        tracks_callback(query_, tracks)

        # (eventually) image
        if track_image_callback:
            debug("Fetching tracks image too")
            for t in tracks:
                def tracks_image_callback_wrapper(rg_id, img):
                    debug(f"Received image for track {t.id} with rg_id = {rg_id}")
                    track_image_callback(t.id, img)
                fetch_release_group_cover(t.release().release_group_id, tracks_image_callback_wrapper)

    musicbrainz.search_recordings(query, recordings_callback_wrapper, limit)


def fetch_mp3_release_group(mp3: Mp3, mp3_release_group_callback, mp3_release_group_image_callback):
    debug(f"fetch_mp3_release_group({mp3})")

    if mp3.fetched_release_group:
        mp3_release_group_callback(mp3, get_release_group(mp3.release_group_id))
    else:
        if not mp3.album:
            print("WARN: no album for mp3")
            mp3.fetched_release_group = True
            # TODO: ... callback?
            return


        def release_groups_callback_wrapper(query_, result: List[MbReleaseGroup]):
            release_groups = [ReleaseGroup(rg) for rg in result]
            for rg in release_groups:
                _add_release_group(rg)

            debug("Figuring out which is the most appropriate release group...")
            if release_groups:
                album_title_distances = [levenshtein.distance(rg.title, mp3.album) for rg in release_groups]
                artist_distances = [levenshtein.distance(rg.artists_string(), mp3.artist) for rg in release_groups]

                weighted_distance = [2 * album_title_distances[i] + artist_distances[i] for i in range(len(release_groups))]

                debug("Computed edit distances for best candidates")
                for idx, rg in enumerate(release_groups):
                    debug(f"[{idx}] (album={rg.title}, artist={rg.artists_string()}): {weighted_distance[idx]}")

                best_release_group = release_groups[min_index(weighted_distance)]

                mp3.fetched_release_group = True
                mp3.release_group_id = best_release_group.id

                mp3.fetched_artist = True

                # TODO: more than an artist
                mp3.artist_id = best_release_group.artist_ids[0]

                mp3_release_group_callback(mp3, best_release_group)

                # (eventually) image
                if mp3_release_group_image_callback:
                    fetch_release_group_cover(best_release_group.id, mp3_release_group_image_callback)


        musicbrainz.search_release_groups(mp3.album, release_groups_callback_wrapper, limit=10)


def fetch_mp3_artist(mp3: Mp3, mp3_artist_callback, mp3_artist_image_callback):
    debug(f"fetch_mp3_artist({mp3})")

    if mp3.fetched_artist:
        mp3_artist_callback(mp3, get_artist(mp3.artist_id))
    else:
        if not mp3.artist:
            print("WARN: no artist for mp3")
            mp3.fetched_artist = True
            # TODO: ... callback?
            return


        def artists_callback_wrapper(query_, result: List[MbReleaseGroup]):
            artists = [Artist(a) for a in result]
            for a in artists:
                _add_artist(a)

            debug("Figuring out which is the most appropriate artist...")
            if artists:
                # album_title_distances = [levenshtein.distance(rg.title, mp3.album) for rg in release_groups]
                artist_distances = [levenshtein.distance(a.name, mp3.artist) for a in artists]

                weighted_distance = [artist_distances[i] for i in range(len(artists))]

                debug("Computed edit distances for best candidates")
                for idx, a in enumerate(artists):
                    debug(f"[{idx}] (artist={a.name}): {weighted_distance[idx]}")

                best_artist = artists[min_index(weighted_distance)]

                mp3.fetched_artist = True
                mp3.artist_id = best_artist.id

                mp3_artist_callback(mp3, best_artist)

                # (eventually) image
                if mp3_artist_image_callback:
                    def artist_callback(_1, _2):
                        pass

                    fetch_artist(best_artist.id, artist_callback, mp3_artist_image_callback)

        musicbrainz.search_artists(mp3.artist, artists_callback_wrapper, limit=10)


def fetch_release_group_cover(release_group_id: str, release_group_cover_callback):
    debug(f"fetch_release_group_cover(release_group_id={release_group_id})")

    rg = get_release_group(release_group_id)
    if rg and rg.fetched_front_cover:
        # cached
        debug(f"Release group ({release_group_id}) cover already fetched, calling release_group_cover_callback directly")
        release_group_cover_callback(release_group_id, rg.front_cover)
    else:
        # actually fetch
        debug(f"Release group ({release_group_id}) cover not fetched yet")
        def release_group_cover_callback_wrapper(rg_id, image):
            _release_groups[rg_id].fetched_front_cover = True
            if image:
                _release_groups[rg_id].front_cover = image
            release_group_cover_callback(rg_id, image)

        musicbrainz.fetch_release_group_cover(release_group_id, preferences.cover_size(), release_group_cover_callback_wrapper,
                                              priority=workers.Worker.PRIORITY_LOW)

def fetch_release_group_releases(release_group_id: str, release_group_releases_callback, release_group_youtube_tracks_callback):
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

            # Now we have to figure which one among the releases is the best one:
            # 1. First of all try to fetch the album from youtube; if we get
            #    pick the release "more similiar" to it

            # Otherwise try to figure out which is the more appropriate
            # release with a combination of these heuristics:
            # 1. If there is at least a "CD", consider only the "CD"
            #    which are probably "more official"
            # 2. Take the release with the number of track nearest to the mean
            # 3. Take the release with the number of track nearest to the mode

            def search_youtube_album_tracks_callback(_1, _2, yttracks: List[YtTrack]):
                rg.fetched_youtube_video_ids = True
                rg.youtube_video_ids = [yt.id for yt in yttracks]

                release_candidates = releases

                releases_track_count = [r.track_count() for r in release_candidates]
                yt_track_count = len(yttracks)
                track_count_modes = multimode(releases_track_count)
                track_count_mean = mean(releases_track_count)

                debug(f"releases_track_count={releases_track_count}")
                debug(f"mean_track_count={track_count_modes}")
                debug(f"modes_track_count={track_count_mean}")

                best_release_candidate = None

                TRACK_NUMBER_FACTOR = 50
                EDIT_DISTANCE_FACTOR = 1
                TRACK_POSITION_DISTANCE_FACTOR = 5

                def compute_track_yttrack_score(t_: Track, yt_: YtTrack):
                    debug(f"compute_track_yttrack_score({t_.title}, {yt_.video_title})")

                    # hack special characters
                    t_title = t_.title.lower()
                    yt_title = yt_.video_title.lower()

                    t_title = t_title.replace("’", "'")
                    yt_title = yt_title.replace("’", "'")

                    t_title = t_title.replace("-", " ")
                    yt_title = yt_title.replace("-", " ")

                    t_title = t_title.replace("‐", " ")
                    yt_title = yt_title.replace("‐", " ")

                    t_title = t_title.replace("_", " ")
                    yt_title = yt_title.replace("_", " ")

                    edit_distance_component = 0
                    track_position_component = 0

                    if t_title in yt_.video_title or yt_title in t_title:
                        edit_distance_component = 0
                    else:
                        edit_distance_component = levenshtein.distance(t_title, yt_title)

                    if t_.track_number is not None and yt_.track_number is not None:
                        track_position_component += abs(t_.track_number - yt_.track_number)

                    edit_distance_component *= EDIT_DISTANCE_FACTOR
                    track_position_component *= TRACK_POSITION_DISTANCE_FACTOR

                    scr = edit_distance_component + track_position_component
                    debug(f"-> {scr} (edit_distance={edit_distance_component} + track_pos={track_position_component}){' *************' if scr == 0 else ''}")
                    return scr

                if yt_track_count:
                    debug(f"Taking main release with tracks more similar to youtube one = {yt_track_count}")
                    def compute_release_score(r):
                        debug(f"Computing release score of {r.title} ({r.id}): {r.track_count()} tracks)")

                        # 1. Same number of track is better
                        # 2. Consider edit distance between the tracks
                        # 3. Consider the difference between the position of the tracks


                        debug("")
                        release_score = abs(r.track_count() - len(yttracks)) * TRACK_NUMBER_FACTOR
                        debug(f"ReleaseScore after track number counting: {release_score}")

                        # compute score based on tracks similarity
                        for t in r.tracks():
                            best_yt_track_score = min([compute_track_yttrack_score(t, y) for y in yttracks])
                            release_score += best_yt_track_score
                            debug(f"Score now is {release_score}")

                        debug(f"Computed release score of {r.title} ({r.id}) = {release_score}")

                        return release_score

                    scores = [compute_release_score(r) for r in release_candidates]

                    for i, sc in enumerate(scores):
                        rc = release_candidates[i]
                        debug(f"Release candidate {rc.title} ({rc.id}) with {release_candidates[i].track_count()} tracks has score = {sc}")

                    best_release_candidate = release_candidates[min_index(scores)]

                    if min(scores) > 0:
                        print(f"WARN: youtube release does not match perfectly musicbrainz release (off by {min(scores)} points)")
                    else:
                        debug(f"Youtube release does match perfectly musicbrainz release")
                else:
                    # fallback: no youtube available

                    # consider only CDs, if possible
                    has_cds = [r.format == "CD" for r in releases].count(True) > 0

                    release_candidates = []

                    if has_cds:
                        for r in releases:
                            candidate = r.format == "CD"
                            debug(f"Release: {r.title}, format={r.format}, track_count={r.track_count()}: candidate {candidate}")

                            if candidate:
                                release_candidates.append(r)
                    else:
                        release_candidates = releases

                    if len(track_count_modes) == 1:
                        # There is only a mode (there could be multiple), take a release with that mode
                        track_count_mode = track_count_modes[0]
                        debug(f"Taking main release with track count equal to the only mode = {track_count_mode}")
                        for r in release_candidates:
                            if r.track_count() == track_count_mode:
                                best_release_candidate = r
                                break
                    else:
                        # Fallback: take the release with the number of track nearest to the mean
                        debug(f"Taking main release with track count nearest to mean = {track_count_mean}")
                        mean_deltas = [abs(tc - track_count_mean) for tc in releases_track_count]
                        best_release_candidate = release_candidates[min_index(mean_deltas)]

                if best_release_candidate:
                    debug(f"Best release candidate: {best_release_candidate.title} ({best_release_candidate.id}) with {best_release_candidate.track_count()} tracks")
                    release_group.main_release_id = best_release_candidate.id

                # Tag track with yttrack ids

                tracks = release_group.main_release().tracks()
                track_names = [t.title for t in tracks]

                debug("Associating yttracks <===> tracks")
                for yttrack_ in yttracks:
                    yttrack = _add_youtube_track(yttrack_)

                    # debug(f"Handling yttrack: {yttrack.video_title}")

                    closest_track_names = get_close_matches(yttrack.video_title, track_names)
                    debug(f"closest_track_names={closest_track_names}")
                    if closest_track_names:
                        closest_tracks = []
                        for closest_track_name in closest_track_names:
                            for t in tracks:
                                if t.title == closest_track_name:
                                    closest_tracks.append(t)
                        closest_tracks_scores = [compute_track_yttrack_score(t, yttrack) for t in closest_tracks]
                        closest_track = closest_tracks[min_index(closest_tracks_scores)]
                        # debug(f"Closest track found: {closest_track.title}")
                        closest_track.fetched_youtube_track = True
                        closest_track.youtube_track_is_official = True
                        closest_track.youtube_track_id = yttrack.id
                        debug(f"'{yttrack.video_title} (#{yttrack.track_number})' <==> '{closest_track.title} (#{closest_track.track_number})' (association score {min(closest_tracks_scores)})")
                    else:
                        print(f"WARN: no close track found for youtube track with title {yttrack.video_title}")

                release_group_releases_callback(release_group_id_, releases)

                if release_group_youtube_tracks_callback:
                    release_group_youtube_tracks_callback(release_group_id_, yttracks)

            if rg.fetched_youtube_video_ids:
                debug("Video ids already fetched")
                search_youtube_album_tracks_callback(None, None, [get_youtube_track(video_id) for video_id in rg.youtube_video_ids])
            else:
                debug("Fetching now video ids")
                ytmusic.search_youtube_album_tracks(rg.artists_string(), rg.title, search_youtube_album_tracks_callback)

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
            artist_image_callback(artist_id, a.image)
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
                        _artists[artist_id__].image = image
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
            release_cover_callback(r_id, image)

        musicbrainz.fetch_release_cover(release_id, preferences.cover_size(), release_cover_callback_wrapper,
                                        priority=workers.Worker.PRIORITY_LOW)

#
# def search_release_youtube_tracks(release_id: str, release_youtube_tracks_callback):
#     debug(f"search_release_youtube_tracks(release_id={release_id})")
#
#     r = get_release(release_id)
#     rg = r.release_group()
#     if r and r.fetched_youtube_video_ids:
#         # cached
#         debug(f"Release ({release_id}) youtube tracks already fetched, calling release_youtube_tracks_callback directly")
#         release_youtube_tracks_callback(release_id, [t.youtube_track() for t in r.tracks()])
#     else:
#         # actually fetch
#         debug(f"Release ({release_id}) youtube tracks not fetched yet")
#         def release_youtube_tracks_callback_wrapper(artist_name, album_title, yttracks: List[YtTrack]):
#             release = _releases[release_id]
#             tracks = release.tracks()
#             track_names = [t.title for t in tracks]
#             release.fetched_youtube_video_ids = True
#
#             for yttrack_ in yttracks:
#                 yttrack = _add_youtube_track(yttrack_)
#
#                 debug(f"Handling yttrack: {yttrack.video_title}")
#
#                 closest_track_names = get_close_matches(yttrack.video_title, track_names)
#                 debug(f"closest_track_names={closest_track_names}")
#                 if closest_track_names:
#                     closest_track_name = closest_track_names[0]
#                     debug(f"Closest track found: {closest_track_name}")
#                     closest_track_index = track_names.index(closest_track_name)
#                     closest_track = tracks[closest_track_index]
#                     closest_track.fetched_youtube_track = True
#                     closest_track.youtube_track_is_official = True
#                     closest_track.youtube_track_id = yttrack.id
#                 else:
#                     print(f"WARN: no close track found for youtube track with title {yttrack.video_title}")
#
#             release_youtube_tracks_callback(release_id, yttracks)
#
#         ytmusic.search_youtube_album_tracks(rg.artists_string(), rg.title, release_youtube_tracks_callback_wrapper)

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


def download_youtube_track(track_id: str,
                           queued_callback, started_callback, progress_callback,
                           finished_callback, canceled_callback, error_callback):
    track = get_track(track_id)
    rg = track.release().release_group()

    if not track.youtube_track_id:
        print(f"WARN: no youtube track associated with track {track.id}")
        return

    def queued_callback_wrapper(video_id: str, track_id_: str):
        queued_callback(track_id, None)

    def started_callback_wrapper(video_id: str, track_id_: str):
        started_callback(track_id, None)

    def progress_callback_wrapper(video_id: str, progress: float, track_id_: str):
        progress_callback(track_id, progress, None)

    def finished_callback_wrapper(video_id: str, output_file: str, track_id_: str):
        track.downloading = False

        def finished_and_loaded_callback(mp3: Mp3):
            finished_callback(track_id, None)

        localsongs.load_mp3_background(output_file, finished_and_loaded_callback, load_image=True)

    def canceled_callback_wrapper(video_id: str, track_id_: str):
        track.downloading = False
        canceled_callback(track_id, None)

    def error_callback_wrapper(video_id: str, error_msg: str, track_id_: str):
        track.downloading = False
        error_callback(track_id, error_msg, None)

    track.downloading = True
    ytdownloader.enqueue_track_download(
        video_id=track.youtube_track().video_id,
        artist=rg.artists_string(),
        album=rg.title,
        song=track.title,
        track_num=track.track_number,
        image=rg.preferred_front_cover(),
        output_directory=preferences.directory(),
        output_format=preferences.output_format(),
        queued_callback=queued_callback_wrapper,
        started_callback=started_callback_wrapper,
        progress_callback=progress_callback_wrapper,
        finished_callback=finished_callback_wrapper,
        canceled_callback=canceled_callback_wrapper,
        error_callback=error_callback_wrapper,
        metadata=True,
        user_data=track.id
    )

def cancel_youtube_track_download(track_id: str):
    track = get_track(track_id)

    if not track.youtube_track_id:
        print(f"WARN: no youtube track associated with track {track.id}")
        return

    ytdownloader.cancel_track_download(track.youtube_track().video_id)
