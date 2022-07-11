import hashlib
import json
import os
import sys
import time
import zlib
from pathlib import Path
from typing import Sequence, Optional, Union

from PyQt5.QtCore import QUrl, QStandardPaths
from PyQt5.QtGui import QPixmap, QIcon, QDesktopServices, QPalette

application_start_time: Optional[int] = None

def make_pixmap_from_data(data, default=None) -> QPixmap:
    pixmap = QPixmap()
    if data:
        pixmap.loadFromData(data)
        return pixmap
    return default

def make_icon_from_data(data, default=None) -> QIcon:
    if data:
        return QIcon(make_pixmap_from_data(data))
    return default

def j(x):
    return json.dumps(x, indent=4)

def current_millis():
    return round(time.time() * 1000)

def initialize_execution_time():
    global application_start_time
    application_start_time = current_millis()

def current_execution_millis():
    return current_millis() - application_start_time

def current_execution_seconds():
    return current_execution_millis() / 1000

def millis_to_long_string(ms, hr_fmt="hr", min_fmt="min", sec_fmt="sec"):
    secs = int(ms / 1000)
    h = int(secs / 3600)
    m = int((secs % 3600) / 60)
    s = secs % 60
    if h:
        return f"{h} {hr_fmt}, {m} {min_fmt}, {s} {sec_fmt}"
    if m:
        return f"{m} {min_fmt}, {s} {sec_fmt}"
    return f"{s} {sec_fmt}"

def millis_to_short_string(ms):
    secs = int(ms / 1000)
    h = int(secs / 3600)
    m = int((secs % 3600) / 60)
    s = secs % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def min_index(sequence: Sequence):
    return sequence.index(min(sequence))

def max_index(sequence: Sequence):
    return sequence.index(max(sequence))

def min_indexes(sequence: Sequence):
    m = min(sequence)
    return [idx for idx, element in enumerate(sequence) if element == m]

def max_indexes(sequence: Sequence):
    m = max(sequence)
    return [idx for idx, element in enumerate(sequence) if element == m]

def sanitize_filename(f: str):
    if not f:
        return f
    f = f.replace("/", "-")
    f = f.replace("? ", " ")
    f = f.replace("?", " ")
    f = f.replace(": ", ", ")
    f = f.replace(":", " ")
    f = f.replace("\"", "")
    return f

def normalize_metadata(something: str):
    if not something:
        return something
    something = something.replace("’", "'")
    something = something.replace("‐", "-")
    something = something.replace("”", "\"")
    something = something.replace("“", "\"")
    return something

def open_url(url: str):
    print(f"INFO: opening {url}")
    QDesktopServices.openUrl(QUrl(url))

def open_folder(directory: Union[Path, str]):
    if isinstance(directory, Path):
        directory = str(directory.absolute())
    print(f"INFO: opening {directory}")
    QDesktopServices.openUrl(QUrl.fromLocalFile(directory))

def app_config_path() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))

def app_cache_path()-> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation))

def app_music_path()-> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.MusicLocation), "MusicDragon")

def is_dark_mode():
    return QPalette().color(QPalette.Window).value() < 128

def get_folder_size(directory: Union[Path, str]) -> int: #KB
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(str(directory)):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def stable_hash(s: str):
    m = hashlib.md5()
    m.update(s.encode())
    return m.hexdigest()

def rangify(a, x, b):
    return max(a, min(x, b))

def is_win():
    return sys.platform.startswith("win")


def crc32(data: bytes):
    return zlib.crc32(data)

class Mergeable:
    def merge(self, other):
        # debug("===== merging =====\n"
        #       f"{(vars(self))}\n"
        #       "------ with -----\n"
        #       f"{(vars(other))}\n"
        # )
        # TODO: recursive check of better()? evaluate len() if hasattr(len) eventually?

        # object overriding better
        if hasattr(self, "better") and hasattr(other, "better"):
            if other.better(self):
                for attr, value in vars(self).items():
                    if hasattr(other, attr):
                        self.__setattr__(attr, other.__getattribute__(attr))
        else:
            # default case
            for attr, value in vars(self).items():
                if attr.startswith("_"):
                    continue # skip private attributes
                if hasattr(other, attr):
                    other_value = other.__getattribute__(attr)
                    # nested object overriding better()
                    if hasattr(value, "better") and hasattr(other_value, "better") and other_value.better(value):
                        self.__setattr__(attr, other_value)
                    # default case
                    else:
                        self.__setattr__(attr, value or other_value)