from typing import Optional

from PyQt5.QtCore import QSettings

_preferences: Optional['QSettings'] = None


def directory():
    return _get_preferences().value("directory", "~/MusicDragon")

def set_directory(value: str):
    _get_preferences().setValue("directory", value)


def cover_size():
    return _get_preferences().value("cover_size", "500")


def set_cover_size(value: str):
    _get_preferences().setValue("cover_size", value)


def output_format():
    return _get_preferences().value("output_format", "{artist}/{album}/{song}.{ext}")


def set_output_format(value: str):
    _get_preferences().setValue("output_format", value)


def _get_preferences():
    global _preferences
    if not _preferences:
        _preferences = QSettings("Docheinstein", "Music Dragon")
    return _preferences
