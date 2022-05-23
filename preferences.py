from typing import Optional

from PyQt5.QtCore import QSettings, QThread

from log import debug

_preferences: Optional[QSettings] = None

def initialize():
    global _preferences
    _preferences = QSettings("Docheinstein", "MusicDragon")
    debug(f"Preferences file path: {_preferences.fileName()}")


# Directory

def directory() -> str:
    return _preferences.value("directory", "~/MusicDragon")

def set_directory(value: str):
    _preferences.setValue("directory", value)

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
