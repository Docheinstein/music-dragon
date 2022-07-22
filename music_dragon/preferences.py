from typing import Optional, Tuple

from PyQt5.QtCore import QSettings, QThread

from music_dragon.utils import app_music_path

_preferences: Optional[QSettings] = None

def initialize():
    global _preferences
    _preferences = QSettings("Docheinstein", "MusicDragon")
    print(f"Preferences path: {_preferences.fileName()}")


# TODO: when the hierarchy of the preferences UI is well defined,
#  set the hierarchy here to so that the INI file respect the UI
# e.g. general/directory

# Geometry
def geometry_and_state() -> Tuple[bytes, bytes]:
    return _preferences.value("geometry"), _preferences.value("state")

def set_geometry_and_state(geom: bytes, state: bytes):
    _preferences.setValue("geometry", geom)
    _preferences.setValue("state", geom)


# Directory

def directory() -> str:
    return _preferences.value("directory", str(app_music_path().absolute()))

def set_directory(value: str):
    _preferences.setValue("directory", value)

# Download directory

def manual_download_directory() -> str:
    return _preferences.value("manual_download_directory", str(app_music_path().absolute()))

def set_manual_download_directory(value: str):
    _preferences.setValue("manual_download_directory", value)

# Cover Size

def cover_size() -> int:
    sz = _preferences.value("cover_size", "500")
    return int(sz) if sz is not None else None


def set_cover_size(value: int):
    _preferences.setValue("cover_size", value if value is not None else None)

# Output format

def output_format() -> str:
    return _preferences.value("output_format", "{artist}/{album}/{song}.{ext}")

def set_output_format(value: str):
    _preferences.setValue("output_format", value)


# Manual output format

def manual_output_format() -> str:
    return _preferences.value("manual_output_format", "{artist}/{album}/{song}.{ext}")


def set_manual_output_format(value: str):
    _preferences.setValue("manual_output_format", value)


# Thread number

def thread_number() -> int:
    th = _preferences.value("thread_number")
    return int(th) if th is not None else QThread.idealThreadCount()


def set_thread_number(value: int):
    _preferences.setValue("thread_number", value)

# Maximum simultaneous downloads

def max_simultaneous_downloads() -> int:
    x = _preferences.value("max_simultaneous_downloads")
    return int(x) if x is not None else max(thread_number() - 1, 1)


def set_max_simultaneous_downloads(value: int):
    _preferences.setValue("max_simultaneous_downloads", value)

# Cache

def is_images_cache_enabled() -> bool:
    x = _preferences.value("cache_images", "1")
    return x == "1"


def set_images_cache_enabled(enabled: bool):
    _preferences.setValue("cache_images", "1" if enabled else "0")


def is_requests_cache_enabled() -> bool:
    x = _preferences.value("cache_requests", "1")
    return x == "1"


def set_requests_cache_enabled(enabled: bool):
    _preferences.setValue("cache_requests", "1" if enabled else "0")


def is_localsongs_cache_enabled() -> bool:
    x = _preferences.value("cache_localsongs", "1")
    return x == "1"


def set_localsongs_cache_enabled(enabled: bool):
    _preferences.setValue("cache_localsongs", "1" if enabled else "0")

# YouTube credentials
# TODO: not plain text?

def set_youtube_email(value: str):
    _preferences.setValue("youtube_email", value)


def get_youtube_email():
    return _preferences.value("youtube_email")


def set_youtube_password(value: str):
    _preferences.setValue("youtube_password", value)


def get_youtube_password():
    return _preferences.value("youtube_password")

# General
def set_preference(key: str, value):
    _preferences.setValue(key, value)

def get_preference(key: str):
    v = _preferences.value(key)
    return int(v) if v is not None else None