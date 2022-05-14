from typing import Optional

from PyQt5.QtCore import QSettings

_preferences: Optional['QSettings'] = None

def set_directory(value: str):
    _get_preferences().setValue("directory", value)


def directory():
    return _get_preferences().value("directory", "~/MusicDragon")

def _get_preferences():
    global _preferences
    if not _preferences:
        _preferences = QSettings("Docheinstein", "Music Dragon")
    return _preferences
