import json
import time

from PyQt5.QtGui import QPixmap, QIcon


def make_pixmap_from_data(data, default=None):
    pixmap = QPixmap()
    if data:
        pixmap.loadFromData(data)
        return pixmap
    return default

def make_icon_from_data(data, default=None):
    if data:
        return QIcon(make_pixmap_from_data(data))
    return default

def j(x):
    return json.dumps(x, indent=4)

def current_millis():
    return round(time.time() * 1000)