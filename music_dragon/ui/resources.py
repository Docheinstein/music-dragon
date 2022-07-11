from typing import Optional

from PyQt5.QtGui import QIcon, QPixmap, QImage

LOCALLY_AVAILABLE_STYLESHEET = "border: 3px solid #32CD32;"
LOCALLY_PARTIALLY_AVAILABLE_STYLESHEET = "border: 3px solid orange;"
LOCALLY_UNAVAILABLE_STYLESHEET = "border: 3px solid gray;"

PILL_HIGHLIGHTED_STYLESHEET = "QLabel {background-color: #1E90FF; border: 1px solid black;border-radius: 5px; font-weight: bold; }"
PILL_UNHIGHLIGHTED_STYLESHEET = "QLabel {background-color: gray; border: 1px solid black;border-radius: 5px; }"


IMAGES_PATH = ":/images/"

COVER_PLACEHOLDER_PATH = f"{IMAGES_PATH}/questionmark.png"
PERSON_PLACEHOLDER_PATH = f"{IMAGES_PATH}/person.jpg"
DOWNLOAD_PATH = f"{IMAGES_PATH}/download.png"
X_PATH = f"{IMAGES_PATH}/x.png"
OPEN_LINK_PATH = f"{IMAGES_PATH}/openlink.png"
PLAY_PATH = f"{IMAGES_PATH}/play.png"
PAUSE_PATH = f"{IMAGES_PATH}/pause.png"
LINK_PATH = f"{IMAGES_PATH}/link.png"
FAVOURITE_PATH = f"{IMAGES_PATH}/favourite.png"
UNFAVOURITE_PATH = f"{IMAGES_PATH}/unfavourite.png"

COVER_PLACEHOLDER_PIXMAP: Optional[QPixmap] = None
PERSON_PLACEHOLDER_PIXMAP: Optional[QPixmap] = None
DOWNLOAD_PIXMAP: Optional[QPixmap] = None
X_PIXMAP: Optional[QPixmap] = None
OPEN_LINK_PIXMAP: Optional[QPixmap] = None
LINK_PIXMAP: Optional[QPixmap] = None
FAVOURITE_PIXMAP: Optional[QPixmap] = None
UNFAVOURITE_PIXMAP: Optional[QPixmap] = None

COVER_PLACEHOLDER_ICON: Optional[QIcon] = None
PERSON_PLACEHOLDER_ICON: Optional[QIcon] = None
DOWNLOAD_ICON: Optional[QIcon] = None
X_ICON: Optional[QIcon] = None
OPEN_LINK_ICON: Optional[QIcon] = None
PLAY_ICON: Optional[QIcon] = None
PAUSE_ICON: Optional[QIcon] = None
LINK_ICON: Optional[QIcon] = None
FAVOURITE_ICON: Optional[QIcon] = None
UNFAVOURITE_ICON: Optional[QIcon] = None

FAVOURITE_IMAGE: Optional[QImage] = None
UNFAVOURITE_IMAGE: Optional[QImage] = None



def initialize():
    global COVER_PLACEHOLDER_PIXMAP
    global PERSON_PLACEHOLDER_PIXMAP
    global DOWNLOAD_PIXMAP
    global OPEN_LINK_PIXMAP
    global X_PIXMAP
    global LINK_PIXMAP
    global FAVOURITE_PIXMAP
    global UNFAVOURITE_PIXMAP
    global COVER_PLACEHOLDER_ICON
    global PERSON_PLACEHOLDER_ICON
    global DOWNLOAD_ICON
    global OPEN_LINK_ICON
    global X_ICON
    global PLAY_ICON
    global PAUSE_ICON
    global LINK_ICON
    global FAVOURITE_ICON
    global UNFAVOURITE_ICON
    global FAVOURITE_IMAGE
    global UNFAVOURITE_IMAGE

    COVER_PLACEHOLDER_PIXMAP = QPixmap(COVER_PLACEHOLDER_PATH)
    PERSON_PLACEHOLDER_PIXMAP = QPixmap(PERSON_PLACEHOLDER_PATH)
    DOWNLOAD_PIXMAP = QPixmap(DOWNLOAD_PATH)
    OPEN_LINK_PIXMAP = QPixmap(OPEN_LINK_PATH)
    X_PIXMAP = QPixmap(X_PATH)
    LINK_PIXMAP = QPixmap(LINK_PATH)
    FAVOURITE_PIXMAP = QPixmap(FAVOURITE_PATH)
    UNFAVOURITE_PIXMAP = QPixmap(UNFAVOURITE_PATH)

    COVER_PLACEHOLDER_ICON = QIcon(COVER_PLACEHOLDER_PATH)
    PERSON_PLACEHOLDER_ICON = QIcon(COVER_PLACEHOLDER_PATH)
    DOWNLOAD_ICON = QIcon(DOWNLOAD_PATH)
    OPEN_LINK_ICON = QIcon(OPEN_LINK_PATH)
    X_ICON = QIcon(X_PATH)
    PLAY_ICON = QIcon(PLAY_PATH)
    PAUSE_ICON = QIcon(PAUSE_PATH)
    LINK_ICON = QIcon(LINK_PATH)
    FAVOURITE_ICON = QIcon(FAVOURITE_PATH)
    UNFAVOURITE_ICON = QIcon(UNFAVOURITE_PATH)

    FAVOURITE_IMAGE = QImage(FAVOURITE_PATH)
    UNFAVOURITE_IMAGE = QImage(UNFAVOURITE_PATH)