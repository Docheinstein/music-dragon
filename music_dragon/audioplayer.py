from typing import Optional

import vlc

from music_dragon.log import debug
from music_dragon.repository import Track

media_player = vlc.MediaPlayer()
media_player_track: Optional[Track] = None

def open_stream(url: str):
    debug(f"Opening stream from url: {url}")
    media_player.set_media(vlc.get_default_instance().media_new(url))

def stream_is_open():
    return media_player.get_media() is not None

def play():
    debug("PLAY")
    media_player.play()

def pause():
    debug("PAUSE")
    media_player.pause()

def is_playing():
    return stream_is_open() and media_player.is_playing()

def current_time():
    return media_player.get_time()


