from music_dragon.log import debug
import vlc

_vlc_instance = vlc.Instance()
media_player = _vlc_instance.media_player_new()

def open_stream(url: str):
    debug(f"Opening audio stream at: {url}")
    if url.startswith("http"):
        media_player.set_media(_vlc_instance.media_new_location(url))
    else:
        media_player.set_media(_vlc_instance.media_new_path(url))


def stream_is_open():
    return media_player.get_media() is not None

def play():
    debug("PLAY")
    media_player.play()

def pause():
    debug("PAUSE")
    media_player.pause()

def get_state():
    s = media_player.get_state()
    debug(f"STATE: {s}")
    return s

def is_playing():
    return get_state() == vlc.State.Playing

def is_paused():
    return get_state() == vlc.State.Paused

def is_ended():
    return get_state() == vlc.State.Ended

def get_time():
    return media_player.get_time()

def set_time(t: int):
    debug(f"Setting time = {t}")
    return media_player.set_time(t)

def set_volume(value: int):
    debug(f"Setting volume = {value}")
    return media_player.audio_set_volume(value) == 0


