from typing import List

import wiki

import musicbrainz
from log import debug
from musicbrainz import MbArtist, MbReleaseGroup, MbRelease, MbTrack

_artists = {}
_release_groups = {}
_releases = {}
_tracks = {}

def get_artist(artist_id) -> MbArtist:
    res = _artists.get(artist_id)
    if res:
        debug(f"get_artist({artist_id}): found")
    else:
        debug(f"get_artist({artist_id}): not found")
    return res

def get_release_group(release_group_id) -> MbReleaseGroup:
    res = _release_groups.get(release_group_id)
    if res:
        debug(f"get_release_group({release_group_id}): found")
    else:
        debug(f"get_release_group({release_group_id}): not found")
    return res

def get_release(release_id) -> MbRelease:
    res = _releases.get(release_id)
    if res:
        debug(f"get_release({release_id}): found")
    else:
        debug(f"get_release({release_id}): not found")
    return res

def get_track(track_id) -> MbTrack:
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
    debug(f"get_entity({entity_id}): not found")
    return None

def search_artists(query, artists_callback, artist_image_callback=None, limit=3):
    def callback_wrapper(param, result: List[MbArtist]):
        for a in result:
            _artists[a.id] = a
        artists_callback(param, result)

        # (eventually) images
        if artist_image_callback:
            def artist_image_callback_wrapper(artist_id, artist):
                _artists[artist_id] = artist  # replace since this is more complete

                def artist_image_callback_wrapper_wikidata(wiki_id, image, artist_id_):
                    debug(f"Pushing image for artist {artist_id_}")
                    _artists[artist_id_].images.add_image(image)
                    artist_image_callback(artist_id_, image)

                if "wikidata" in artist.urls:
                    wiki.fetch_wikidata_image(artist.urls["wikidata"].split("/")[-1], artist_image_callback_wrapper_wikidata, user_data=artist.id)


            for a in result:
                musicbrainz.fetch_artist(a.id, artist_image_callback_wrapper)

    musicbrainz.search_artists(query, callback_wrapper, limit)

def search_release_groups(query, release_groups_callback, release_group_main_release_callback=None, release_group_image_callback=None, limit=3):
    def release_groups_callback_wrapper(param, result: List[MbReleaseGroup]):
        for rg in result:
            _release_groups[rg.id] = rg
        release_groups_callback(param, result)

        # (eventually) releases
        if release_group_main_release_callback:
            def fetch_release_group_main_release_wrapper(rg_id, main_release: MbRelease):
                _release_groups[rg_id].main_release_id = main_release.id
                _releases[main_release.id] = main_release
                release_group_main_release_callback(rg_id, main_release)

            for rg in result:
                musicbrainz.fetch_release_group_main_release(rg.id, fetch_release_group_main_release_wrapper)

        # (eventually) images
        if release_group_image_callback:
            def release_group_image_callback_wrapper(rg_id, image):
                _release_groups[rg_id].images.add_image(image)
                release_group_image_callback(rg_id, image)

            for rg in result:
                musicbrainz.fetch_release_group_cover(rg.id, release_group_image_callback_wrapper)


    musicbrainz.search_release_groups(query, release_groups_callback_wrapper, limit)


# def fetch_artist(artist_id, callback, image_callback=None):
#     def callback_wrapper(param, result: MbArtist):
#         artists[result.id] = result # replace since this is better
#         callback(param, result)
#
#         if image_callback:
#             def image_callback_wrapper(wiki_id, artist_id_, image):
#                 artists[artist_id].images.add_image(image)
#                 image_callback(artist_id_, image)
#
#             if "wikidata" in result.urls:
#                 wiki.fetch_wikidata_image(result.urls["wikidata"], artist_id, image_callback_wrapper)
#
#     musicbrainz.fetch_artist(artist_id, callback_wrapper)
#
