from typing import Optional

from PyQt5.QtCore import QSettings

_preferences: Optional['QSettings'] = None

def set_download_directory(value: str):
    _get_preferences().setValue("downloadDirectory", value)


def download_directory():
    return _get_preferences().value("downloadDirectory", "~/MusicDragon")

def _get_preferences():
    global _preferences
    if not _preferences:
        _preferences = QSettings("Docheinstein", "Music Dragon")
    return _preferences
