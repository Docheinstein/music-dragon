from typing import Optional

from PyQt5.QtCore import QSettings

_preferences: Optional[QSettings] = None

def initialize():
    global _preferences
    _preferences = QSettings("Docheinstein", "Music Dragon")


# Directory

def directory():
    return _preferences.value("directory", "~/MusicDragon")

def set_directory(value: str):
    _preferences.setValue("directory", value)

# Cover Size

def cover_size():
    return _preferences.value("cover_size", "500")


def set_cover_size(value: str):
    _preferences.setValue("cover_size", value)

# Output format

def output_format():
    return _preferences.value("output_format", "{artist}/{album}/{song}.{ext}")


def set_output_format(value: str):
    _preferences.setValue("output_format", value)
