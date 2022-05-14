import json

from PyQt5.QtGui import QPixmap, QIcon


def make_pixmap_from_data(data):
    pixmap = QPixmap()
    if data:
        pixmap.loadFromData(data)
    return pixmap

def make_icon_from_data(data):
    return QIcon(make_pixmap_from_data(data))

def j(x):
    return json.dumps(x, indent=4)