import json
import time
from pathlib import Path
from typing import Sequence, Optional, Union

from PyQt5.QtCore import QUrl
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
    return f.replace("/", "-")

def open_url(url: str):
    QDesktopServices.openUrl(QUrl(url))

def open_folder(directory: Union[Path, str]):
    if isinstance(directory, Path):
        directory = str(directory.absolute())
    QDesktopServices.openUrl(QUrl.fromLocalFile(directory))


def is_dark_mode():
    return QPalette().color(QPalette.Window).value() < 128

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