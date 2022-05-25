import json
import time
from typing import Sequence

from PyQt5.QtGui import QPixmap, QIcon

from log import debug


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

def min_index(sequence: Sequence):
    return sequence.index(min(sequence))

class Mergeable:
    def merge(self, other):
        debug("===== merging =====\n"
              f"{(vars(self))}\n"
              "------ with -----\n"
              f"{(vars(other))}\n"
        )
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