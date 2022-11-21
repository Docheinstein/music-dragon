import sys
import unicodedata
from typing import Optional, List, Dict

import Levenshtein as levenshtein
from PyQt5.QtCore import pyqtSignal
from ytmusicapi import YTMusic

from music_dragon import workers
from music_dragon.log import debug
from music_dragon.utils import j, Mergeable, max_index, normalize_metadata
from music_dragon.workers import Worker

_yt: Optional[YTMusic] = None

def initialize():
    global _yt
    try:
        _yt = YTMusic()
    except Exception as e:
        print(f"ERROR: failed to initialize YTMusic: {e}", file=sys.stderr)
        _yt = None
# Hack ytmusicapi.get_playist since fails if no header is there

DUMMY_HEADER = {
    "musicDetailHeaderRenderer": {
"title": {
    "runs": [
        {
            "text": "Senjutsu"
        }
    ]
},
"subtitle": {
    "runs": [
        {
            "text": "Playlist"
        },
        {
            "text": " \u2022 "
        },
        {
            "text": "Iron Maiden",
            "navigationEndpoint": {
                "clickTrackingParams": "CAEQ99wCIhMIopKJt46j-AIV1t4RCB1Smwih",
                "browseEndpoint": {
                    "browseId": "UC0zbzp6x7zR8u0LhanNWFyw",
                    "browseEndpointContextSupportedConfigs": {
                        "browseEndpointContextMusicConfig": {
                            "pageType": "MUSIC_PAGE_TYPE_USER_CHANNEL"
                        }
                    }
                }
            }
        },
        {
            "text": " \u2022 "
        },
        {
            "text": "2021"
        }
    ]
},
"menu": {
    "menuRenderer": {
        "items": [
            {
                "menuNavigationItemRenderer": {
                    "text": {
                        "runs": [
                            {
                                "text": "Start radio"
                            }
                        ]
                    },
                    "icon": {
                        "iconType": "MIX"
                    },
                    "navigationEndpoint": {
                        "clickTrackingParams": "CA8Qm_MFGAAiEwiikom3jqP4AhXW3hEIHVKbCKE=",
                        "watchPlaylistEndpoint": {
                            "playlistId": "RDAMPLPLCfCU1Ok5NVslWB4mi0MtVsvpjILpFy-p",
                            "params": "wAEB"
                        }
                    },
                    "trackingParams": "CA8Qm_MFGAAiEwiikom3jqP4AhXW3hEIHVKbCKE="
                }
            },
            {
                "menuServiceItemRenderer": {
                    "text": {
                        "runs": [
                            {
                                "text": "Play next"
                            }
                        ]
                    },
                    "icon": {
                        "iconType": "QUEUE_PLAY_NEXT"
                    },
                    "serviceEndpoint": {
                        "clickTrackingParams": "CA0Qvu4FGAEiEwiikom3jqP4AhXW3hEIHVKbCKE=",
                        "queueAddEndpoint": {
                            "queueTarget": {
                                "playlistId": "PLCfCU1Ok5NVslWB4mi0MtVsvpjILpFy-p"
                            },
                            "queueInsertPosition": "INSERT_AFTER_CURRENT_VIDEO",
                            "commands": [
                                {
                                    "clickTrackingParams": "CA0Qvu4FGAEiEwiikom3jqP4AhXW3hEIHVKbCKE=",
                                    "addToToastAction": {
                                        "item": {
                                            "notificationTextRenderer": {
                                                "successResponseText": {
                                                    "runs": [
                                                        {
                                                            "text": "Playlist will play next"
                                                        }
                                                    ]
                                                },
                                                "trackingParams": "CA4QyscDIhMIopKJt46j-AIV1t4RCB1Smwih"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "trackingParams": "CA0Qvu4FGAEiEwiikom3jqP4AhXW3hEIHVKbCKE="
                }
            },
            {
                "menuServiceItemRenderer": {
                    "text": {
                        "runs": [
                            {
                                "text": "Add to queue"
                            }
                        ]
                    },
                    "icon": {
                        "iconType": "ADD_TO_REMOTE_QUEUE"
                    },
                    "serviceEndpoint": {
                        "clickTrackingParams": "CAsQ--8FGAIiEwiikom3jqP4AhXW3hEIHVKbCKE=",
                        "queueAddEndpoint": {
                            "queueTarget": {
                                "playlistId": "PLCfCU1Ok5NVslWB4mi0MtVsvpjILpFy-p"
                            },
                            "queueInsertPosition": "INSERT_AT_END",
                            "commands": [
                                {
                                    "clickTrackingParams": "CAsQ--8FGAIiEwiikom3jqP4AhXW3hEIHVKbCKE=",
                                    "addToToastAction": {
                                        "item": {
                                            "notificationTextRenderer": {
                                                "successResponseText": {
                                                    "runs": [
                                                        {
                                                            "text": "Playlist added to queue"
                                                        }
                                                    ]
                                                },
                                                "trackingParams": "CAwQyscDIhMIopKJt46j-AIV1t4RCB1Smwih"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "trackingParams": "CAsQ--8FGAIiEwiikom3jqP4AhXW3hEIHVKbCKE="
                }
            },
            {
                "menuNavigationItemRenderer": {
                    "text": {
                        "runs": [
                            {
                                "text": "Add to playlist"
                            }
                        ]
                    },
                    "icon": {
                        "iconType": "ADD_TO_PLAYLIST"
                    },
                    "navigationEndpoint": {
                        "clickTrackingParams": "CAkQw5QGGAMiEwiikom3jqP4AhXW3hEIHVKbCKE=",
                        "modalEndpoint": {
                            "modal": {
                                "modalWithTitleAndButtonRenderer": {
                                    "title": {
                                        "runs": [
                                            {
                                                "text": "Save this for later"
                                            }
                                        ]
                                    },
                                    "content": {
                                        "runs": [
                                            {
                                                "text": "Make playlists and share them after signing in"
                                            }
                                        ]
                                    },
                                    "button": {
                                        "buttonRenderer": {
                                            "style": "STYLE_BLUE_TEXT",
                                            "isDisabled": False,
                                            "text": {
                                                "runs": [
                                                    {
                                                        "text": "Sign in"
                                                    }
                                                ]
                                            },
                                            "navigationEndpoint": {
                                                "clickTrackingParams": "CAoQ8FsiEwiikom3jqP4AhXW3hEIHVKbCKE=",
                                                "signInEndpoint": {
                                                    "hack": True
                                                }
                                            },
                                            "trackingParams": "CAoQ8FsiEwiikom3jqP4AhXW3hEIHVKbCKE="
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "trackingParams": "CAkQw5QGGAMiEwiikom3jqP4AhXW3hEIHVKbCKE="
                }
            },
            {
                "menuNavigationItemRenderer": {
                    "text": {
                        "runs": [
                            {
                                "text": "Share"
                            }
                        ]
                    },
                    "icon": {
                        "iconType": "SHARE"
                    },
                    "navigationEndpoint": {
                        "clickTrackingParams": "CAgQkfsFGAQiEwiikom3jqP4AhXW3hEIHVKbCKE=",
                        "shareEntityEndpoint": {
                            "serializedShareEntity": "EiJQTENmQ1UxT2s1TlZzbFdCNG1pME10VnN2cGpJTHBGeS1w",
                            "sharePanelType": "SHARE_PANEL_TYPE_UNIFIED_SHARE_PANEL"
                        }
                    },
                    "trackingParams": "CAgQkfsFGAQiEwiikom3jqP4AhXW3hEIHVKbCKE="
                }
            }
        ],
        "trackingParams": "CAQQpzsiEwiikom3jqP4AhXW3hEIHVKbCKE=",
        "topLevelButtons": [
            {
                "buttonRenderer": {
                    "style": "STYLE_DARK_ON_WHITE",
                    "size": "SIZE_DEFAULT",
                    "text": {
                        "runs": [
                            {
                                "text": "Shuffle"
                            }
                        ]
                    },
                    "icon": {
                        "iconType": "MUSIC_SHUFFLE"
                    },
                    "navigationEndpoint": {
                        "clickTrackingParams": "CAcQ8FsYBSITCKKSibeOo_gCFdbeEQgdUpsIoQ==",
                        "watchPlaylistEndpoint": {
                            "playlistId": "PLCfCU1Ok5NVslWB4mi0MtVsvpjILpFy-p",
                            "params": "wAEB8gECKAE%3D"
                        }
                    },
                    "accessibility": {
                        "label": "Shuffle"
                    },
                    "trackingParams": "CAcQ8FsYBSITCKKSibeOo_gCFdbeEQgdUpsIoQ==",
                    "accessibilityData": {
                        "accessibilityData": {
                            "label": "Shuffle"
                        }
                    }
                }
            },
            {
                "toggleButtonRenderer": {
                    "isToggled": False,
                    "isDisabled": False,
                    "defaultIcon": {
                        "iconType": "LIBRARY_ADD"
                    },
                    "defaultText": {
                        "runs": [
                            {
                                "text": "Add to library"
                            }
                        ],
                        "accessibility": {
                            "accessibilityData": {
                                "label": "Add to library"
                            }
                        }
                    },
                    "toggledIcon": {
                        "iconType": "LIBRARY_REMOVE"
                    },
                    "toggledText": {
                        "runs": [
                            {
                                "text": "Remove from library"
                            }
                        ],
                        "accessibility": {
                            "accessibilityData": {
                                "label": "Remove from library"
                            }
                        }
                    },
                    "trackingParams": "CAUQmE0YBiITCKKSibeOo_gCFdbeEQgdUpsIoQ==",
                    "defaultNavigationEndpoint": {
                        "clickTrackingParams": "CAUQmE0YBiITCKKSibeOo_gCFdbeEQgdUpsIoQ==",
                        "modalEndpoint": {
                            "modal": {
                                "modalWithTitleAndButtonRenderer": {
                                    "title": {
                                        "runs": [
                                            {
                                                "text": "Save this for later"
                                            }
                                        ]
                                    },
                                    "content": {
                                        "runs": [
                                            {
                                                "text": "Add favorites to your library after signing in"
                                            }
                                        ]
                                    },
                                    "button": {
                                        "buttonRenderer": {
                                            "style": "STYLE_BLUE_TEXT",
                                            "isDisabled": False,
                                            "text": {
                                                "runs": [
                                                    {
                                                        "text": "Sign in"
                                                    }
                                                ]
                                            },
                                            "navigationEndpoint": {
                                                "clickTrackingParams": "CAYQ8FsiEwiikom3jqP4AhXW3hEIHVKbCKE=",
                                                "signInEndpoint": {
                                                    "hack": True
                                                }
                                            },
                                            "trackingParams": "CAYQ8FsiEwiikom3jqP4AhXW3hEIHVKbCKE="
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ],
        "accessibility": {
            "accessibilityData": {
                "label": "Action menu"
            }
        }
    }
},
"thumbnail": {
    "croppedSquareThumbnailRenderer": {
        "thumbnail": {
            "thumbnails": [
                {
                    "url": "https://yt3.ggpht.com/KORj1iCLlXa2kQh7HB8Q2MFctximcBvlWqdhU5LOM0npJkLe14oSFhTd1GDsvdSwx1mPsjZX_Bs=s192",
                    "width": 192,
                    "height": 192
                },
                {
                    "url": "https://yt3.ggpht.com/KORj1iCLlXa2kQh7HB8Q2MFctximcBvlWqdhU5LOM0npJkLe14oSFhTd1GDsvdSwx1mPsjZX_Bs=s576",
                    "width": 576,
                    "height": 576
                },
                {
                    "url": "https://yt3.ggpht.com/KORj1iCLlXa2kQh7HB8Q2MFctximcBvlWqdhU5LOM0npJkLe14oSFhTd1GDsvdSwx1mPsjZX_Bs=s1200",
                    "width": 1200,
                    "height": 1200
                }
            ]
        },
        "trackingParams": "CAMQymQiEwiikom3jqP4AhXW3hEIHVKbCKE="
    }
},
"trackingParams": "CAEQ99wCIhMIopKJt46j-AIV1t4RCB1Smwih",
"description": {
    "runs": [
        {
            "text": "New album - out now!"
        }
    ]
},
"moreButton": {
    "toggleButtonRenderer": {
        "isToggled": False,
        "isDisabled": False,
        "defaultIcon": {
            "iconType": "EXPAND"
        },
        "defaultText": {
            "runs": [
                {
                    "text": "More"
                }
            ]
        },
        "toggledIcon": {
            "iconType": "COLLAPSE"
        },
        "toggledText": {
            "runs": [
                {
                    "text": "Less"
                }
            ]
        },
        "trackingParams": "CAIQmE0iEwiikom3jqP4AhXW3hEIHVKbCKE="
    }
},
"secondSubtitle": {
    "runs": [
        {
            "text": "18 songs"
        },
        {
            "text": " \u2022 "
        },
        {
            "text": "1 hour, 55 minutes"
        }
    ]
}
}
}

def ytmusicapi_get_playlist(yt_: YTMusic, playlistId, limit=100):
    """
    Returns a list of playlist items

    :param playlistId: Playlist id
    :param limit: How many songs to return. Default: 100
    :return: Dictionary with information about the playlist.
        The key ``tracks`` contains a List of playlistItem dictionaries

    Each item is in the following format::

        {
          "id": "PLQwVIlKxHM6qv-o99iX9R85og7IzF9YS_",
          "privacy": "PUBLIC",
          "title": "New EDM This Week 03/13/2020",
          "thumbnails": [...]
          "description": "Weekly r/EDM new release roundup. Created with github.com/sigma67/spotifyplaylist_to_gmusic",
          "author": "sigmatics",
          "year": "2020",
          "duration": "6+ hours",
          "duration_seconds": 52651,
          "trackCount": 237,
          "tracks": [
            {
              "videoId": "bjGppZKiuFE",
              "title": "Lost",
              "artists": [
                {
                  "name": "Guest Who",
                  "id": "UCkgCRdnnqWnUeIH7EIc3dBg"
                },
                {
                  "name": "Kate Wild",
                  "id": "UCwR2l3JfJbvB6aq0RnnJfWg"
                }
              ],
              "album": {
                "name": "Lost",
                "id": "MPREb_PxmzvDuqOnC"
              },
              "duration": "2:58",
              "likeStatus": "INDIFFERENT",
              "thumbnails": [...],
              "isAvailable": True,
              "isExplicit": False,
              "feedbackTokens": {
                "add": "AB9zfpJxtvrU...",
                "remove": "AB9zfpKTyZ..."
            }
          ]
        }

    The setVideoId is the unique id of this playlist item and
    needed for moving/removing playlist items
    """
    from ytmusicapi.helpers import to_int, sum_total_duration
    from ytmusicapi.navigation import RELOAD_CONTINUATION as RELOAD_CONTINUATION
    from ytmusicapi.navigation import MUSIC_SHELF as MUSIC_SHELF
    from ytmusicapi.navigation import SUBTITLE3 as SUBTITLE3
    from ytmusicapi.navigation import NAVIGATION_BROWSE_ID as NAVIGATION_BROWSE_ID
    from ytmusicapi.navigation import SUBTITLE2 as SUBTITLE2
    from ytmusicapi.navigation import DESCRIPTION as DESCRIPTION
    from ytmusicapi.navigation import THUMBNAIL_CROPPED as THUMBNAIL_CROPPED
    from ytmusicapi.navigation import TITLE_TEXT as TITLE_TEXT
    from ytmusicapi.navigation import SECTION_LIST_ITEM as SECTION_LIST_ITEM
    from ytmusicapi.navigation import SINGLE_COLUMN_TAB as SINGLE_COLUMN_TAB
    from ytmusicapi.navigation import nav as nav
    from ytmusicapi.parsers.playlists import parse_playlist_items
    from ytmusicapi.continuations import get_continuations

    browseId = "VL" + playlistId if not playlistId.startswith("VL") else playlistId
    body = {'browseId': browseId}
    endpoint = 'browse'
    response = yt_._send_request(endpoint, body)

    results = nav(response,
                  SINGLE_COLUMN_TAB + SECTION_LIST_ITEM + ['musicPlaylistShelfRenderer'])
    # ======= HACK =========
    if "playlistId" not in results:
        results["playlistId"] = playlistId
    if "header" not in response:
        response["header"] = DUMMY_HEADER
    playlist = {'id': results['playlistId']}

    own_playlist = 'musicEditablePlaylistDetailHeaderRenderer' in response['header']
    if not own_playlist:
        header = response['header']['musicDetailHeaderRenderer']
        playlist['privacy'] = 'PUBLIC'
    else:
        header = response['header']['musicEditablePlaylistDetailHeaderRenderer']
        playlist['privacy'] = header['editHeader']['musicPlaylistEditHeaderRenderer']['privacy']
        # print(header)
        header = header['header']['musicDetailHeaderRenderer']

    playlist['title'] = nav(header, TITLE_TEXT)
    playlist['thumbnails'] = nav(header, THUMBNAIL_CROPPED)
    playlist["description"] = nav(header, DESCRIPTION, True)
    run_count = len(header['subtitle']['runs'])
    if run_count > 1:
        playlist['author'] = {
            'name': nav(header, SUBTITLE2),
            'id': nav(header, ['subtitle', 'runs', 2] + NAVIGATION_BROWSE_ID, True)
        }
        if run_count == 5:
            playlist['year'] = nav(header, SUBTITLE3)

    song_count = to_int(
        unicodedata.normalize("NFKD", header['secondSubtitle']['runs'][0]['text']))
    if len(header['secondSubtitle']['runs']) > 1:
        playlist['duration'] = header['secondSubtitle']['runs'][2]['text']

    playlist['trackCount'] = song_count
    playlist['suggestions_token'] = nav(
        response, SINGLE_COLUMN_TAB + ['sectionListRenderer', 'contents', 1] + MUSIC_SHELF
        + RELOAD_CONTINUATION, True)

    playlist['tracks'] = []
    if song_count > 0:
        playlist['tracks'].extend(parse_playlist_items(results['contents']))
        songs_to_get = min(limit, song_count)

        if 'continuations' in results:
            request_func = lambda additionalParams: yt_._send_request(
                endpoint, body, additionalParams)
            parse_func = lambda contents: parse_playlist_items(contents)
            playlist['tracks'].extend(
                get_continuations(results, 'musicPlaylistShelfContinuation',
                                  songs_to_get - len(playlist['tracks']), request_func,
                                  parse_func))

    playlist['duration_seconds'] = sum_total_duration(playlist)
    return playlist

class YtTrack(Mergeable):
    def __init__(self, yt_track: dict):
        self.id = None
        self.video_id = None
        self.video_title = None
        self.song = None
        self.album = None
        self.artists = None
        self.track_number = None
        self.year = None
        self.streams = []
        self.streams_fetched = False

        if yt_track:
            self.id = yt_track.get("videoId") or yt_track.get("id")
            self.video_id = self.id
            self.video_title = normalize_metadata(yt_track.get("title"))
            self.song = normalize_metadata(yt_track.get("track")) or self.video_title
            self.album = normalize_metadata(yt_track["album"]["name"]) if "album" in yt_track and isinstance(yt_track["album"], dict) \
                                            else normalize_metadata(yt_track.get("album"))
            artists = [normalize_metadata(a["name"]) for a in yt_track["artists"]] if "artists" in yt_track \
                else [normalize_metadata(yt_track.get("artist"))]

            # Don't know why, but sometimes yt_downloader returns something like
            # 'artist': 'Nobuo Uematsu, Nobuo Uematsu, Nobuo Uematsu'
            # try to fix this
            self.artists = []
            try:
                for a in artists:
                    tokens = [s.strip() for s in a.split(",")]
                    n_tokens = len(tokens)
                    tokens = set(tokens)
                    if len(tokens) != n_tokens:
                        a = ", ".join(tokens)
                    # else: keep the original string
                    self.artists.append(a)
            except Exception as e:
                # TODO: AttributeError: 'NoneType' object has no attribute 'split'
                print(f"WARN: exception: {e}")
                self.artists = artists

            self.track_number = yt_track.get("track_number")
            self.year = yt_track.get("year")


    def merge(self, other):
        # handle flags apart
        streams_fetched = self.streams_fetched or other.streams_fetched
        super().merge(other)
        self.streams_fetched = streams_fetched

# ========== SEARCH YOUTUBE TRACK ===========
# Search youtube track for a given query
# ===========================================

class SearchYoutubeTrackWorker(Worker):
    result = pyqtSignal(str, dict)

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
            self.result.emit(self.query, result[0])

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
    result = pyqtSignal(str, str, dict)

    def __init__(self, artist_name: str, album_title: str):
        super().__init__()
        self.artist_name = artist_name
        self.album_title = album_title

    def run(self) -> None:
        def get_closest(query_raw, elements: List[dict], field: str) -> Optional[dict]:
            query = query_raw.lower()
            scores = [0] * len(elements)

            # Figure out the best match based on
            # 1. The query contains the target or the target contains the query
            # 2. Edit distance
            for i, e in enumerate(elements):
                e_name_raw = e[field]
                e_name = e_name_raw.lower()

                if query_raw == e_name_raw:
                    scores[i] += 4000
                elif query == e_name:
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

        result = {}

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
            try:
                artist_details = _yt.get_artist(artist["browseId"])
                debug(
                    "=== yt_get_artist ==="
                    f"{j(artist_details)}"
                    "======================"
                )

                if "albums" in artist_details:
                    if "params" in artist_details["albums"]:  # must be fetched
                        debug(f"YOUTUBE_MUSIC: get_artist_albums(artist='{artist['browseId']}')")
                        artist_albums = _yt.get_artist_albums(artist["browseId"], artist_details["albums"]["params"])
                        debug(
                            "=== get_artist_albums ==="
                            f"{j(artist_albums)}"
                            "======================"
                        )
                    else:  # already there
                        artist_albums = artist_details["albums"]["results"]

                    album = get_closest_album(album_query, artist_albums)

                    if album:
                        debug(f"Closest album found: {album['title']}")

                        album_id = album["browseId"]

                        debug(f"YOUTUBE_MUSIC: get_album: '{album_id}'")
                        album_details = _yt.get_album(album_id)
                        debug(
                            "=== get_album ==="
                            f"{j(result)}"
                            "======================"
                        )

                        # Prefer playlist tracks against album tracks (more reliable)
                        playlist_id = album_details.get("audioPlaylistId")
                        if playlist_id:
                            try:
                                debug(f"YOUTUBE_MUSIC: get_playlist: '{playlist_id}'")
                                result = ytmusicapi_get_playlist(_yt, playlist_id)
                                debug(
                                    "=== get_playlist ==="
                                    f"{j(result)}"
                                    "======================"
                                )
                                result["audioPlaylistId"] = playlist_id
                            except Exception as e:
                                # Fallback: use album tracks
                                debug(f"Failed to retrieve playlist, trying with album. error: {e}")
                                result = album_details

                        for idx, yttrack in enumerate(result["tracks"]):
                            # hack
                            yttrack["track_number"] = idx + 1

                            yttrack["album"] = {
                                "id": album['browseId'],
                                "name": album["title"]
                            }
            except:
                print(f"WARN: failed to retrieve artist details for artist {artist['browseId']}")

            else:
                print(f"WARN: no album close to '{album_query}' for artist '{artist_query}'")
        else:
            print(f"WARN: no artist close to '{artist_query}'")

        self.result.emit(self.artist_name, self.album_title, result)


def search_youtube_album(artist_name: str, album_title: str, callback, priority=workers.Worker.PRIORITY_NORMAL):
    if _yt:
        worker = SearchYoutubeAlbumTracksWorker(artist_name, album_title)
        worker.priority = priority
        worker.result.connect(callback)
        workers.schedule(worker)

# ========== FETCH YOUTUBE TRACK ===========
# Fetch youtube track
# ===========================================

class FetchYoutubeTrackWorker(Worker):
    result = pyqtSignal(str, dict)

    def __init__(self, video_id: str):
        super().__init__()
        self.video_id = video_id

    def run(self) -> None:
        debug(f"YOUTUBE_MUSIC: get_song: '{self.video_id}'")
        result = _yt.get_song(self.video_id)
        debug(
            "=== get_song ==="
            f"{j(result)}"
            "======================"
        )
        if result:
            self.result.emit(self.video_id, result)

def fetch_track_info(video_id: str, callback, priority=workers.Worker.PRIORITY_NORMAL):
    if _yt:
        worker = FetchYoutubeTrackWorker(video_id)
        worker.priority = priority
        worker.result.connect(callback)
        workers.schedule(worker)


# ========== FETCH YOUTUBE PLAYLIST ===========
# Fetch youtube playlist
# ===========================================

class FetchYoutubeAlbumOrPlaylistWorker(Worker):
    result = pyqtSignal(str, dict)

    def __init__(self, playlist_id: str):
        super().__init__()
        self.playlist_id = playlist_id

    def run(self) -> None:
        # The albums can't be retrieve with get_playlist
        debug(f"YOUTUBE_MUSIC: get_album_browse_id: '{self.playlist_id}'")

        result = None

        try:
            debug(f"YOUTUBE_MUSIC: get_playlist: '{self.playlist_id}'")
            result = ytmusicapi_get_playlist(_yt, self.playlist_id)
            debug(
                "=== get_playlist ==="
                f"{j(result)}"
                "======================"
            )
        except Exception as e:
            debug(f"Failed to retrieve playlist, trying with album")
            album_id = _yt.get_album_browse_id(self.playlist_id)
            if album_id:
                debug(f"YOUTUBE_MUSIC: get_album: '{album_id}'")
                result = _yt.get_album(album_id)
                debug(
                    "=== get_album ==="
                    f"{j(result)}"
                    "======================"
            )

        if result:
            self.result.emit(self.playlist_id, result)

def fetch_album_or_playlist_info(playlist_id: str, callback, priority=workers.Worker.PRIORITY_NORMAL):
    if _yt:
        worker = FetchYoutubeAlbumOrPlaylistWorker(playlist_id)
        worker.priority = priority
        worker.result.connect(callback)
        workers.schedule(worker)
