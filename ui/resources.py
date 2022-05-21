from typing import Optional

from PyQt5.QtGui import QIcon, QPixmap


IMAGES_PATH = "res/images/"

COVER_PLACEHOLDER_PATH = f"{IMAGES_PATH}/questionmark.png"
PERSON_PLACEHOLDER_PATH = f"{IMAGES_PATH}/person.jpg"
DOWNLOAD_PATH = f"{IMAGES_PATH}/download.png"
OPEN_LINK_PATH = f"{IMAGES_PATH}/openlink.png"

COVER_PLACEHOLDER_PIXMAP: Optional[QPixmap] = None
PERSON_PLACEHOLDER_PIXMAP: Optional[QPixmap] = None
DOWNLOAD_PIXMAP: Optional[QPixmap] = None
OPEN_LINK_PIXMAP: Optional[QPixmap] = None

COVER_PLACEHOLDER_ICON: Optional[QIcon] = None
PERSON_PLACEHOLDER_ICON: Optional[QIcon] = None
DOWNLOAD_ICON: Optional[QIcon] = None
OPEN_LINK_ICON: Optional[QIcon] = None

def initialize():
    global COVER_PLACEHOLDER_PIXMAP
    global PERSON_PLACEHOLDER_PIXMAP
    global DOWNLOAD_PIXMAP
    global OPEN_LINK_PIXMAP
    global COVER_PLACEHOLDER_ICON
    global PERSON_PLACEHOLDER_ICON
    global DOWNLOAD_ICON
    global OPEN_LINK_ICON

    COVER_PLACEHOLDER_PIXMAP = QPixmap(COVER_PLACEHOLDER_PATH)
    PERSON_PLACEHOLDER_PIXMAP = QPixmap(PERSON_PLACEHOLDER_PATH)
    DOWNLOAD_PIXMAP = QPixmap(DOWNLOAD_PATH)
    OPEN_LINK_PIXMAP = QPixmap(OPEN_LINK_PATH)

    COVER_PLACEHOLDER_ICON = QIcon(COVER_PLACEHOLDER_PATH)
    PERSON_PLACEHOLDER_ICON = QIcon(COVER_PLACEHOLDER_PATH)
    DOWNLOAD_ICON = QIcon(DOWNLOAD_PATH)
    OPEN_LINK_ICON = QIcon(OPEN_LINK_PATH)