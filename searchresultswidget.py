from typing import Optional, List

from PyQt5.QtCore import QSize, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QListWidget, QWidget, QLabel, QSizePolicy, QHBoxLayout, QListWidgetItem, \
    QVBoxLayout

import globals
import repository
from log import debug
from repository import Artist, ReleaseGroup
from ui.listwidgetmodelview import ListWidgetModelViewItem, ListWidgetModel, ListWidgetModelView
from utils import make_pixmap_from_data


class SearchResultsItemWidget(ListWidgetModelViewItem):
    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.subtitle: Optional[QLabel] = None
            self.layout = None
            self.inner_layout = None

    def __init__(self, item_id):
        super().__init__()
        self.result_id = item_id
        self.result = repository.get_entity(self.result_id)
        if not self.result:
            print(f"WARN: no entity for id '{item_id}'")
            return

        self.ui = SearchResultsItemWidget.Ui()
        self.setup()
        self.invalidate()

    def setup(self):
        # cover
        self.ui.cover = QLabel()
        self.ui.cover.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ui.cover.setMaximumSize(QSize(80, 80))
        self.ui.cover.setScaledContents(True)

        # title
        self.ui.title = QLabel()
        self.ui.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        font = self.ui.title.font()
        font.setBold(True)
        font.setPointSize(14)
        self.ui.title.setFont(font)

        # subtitle
        self.ui.subtitle = QLabel()
        self.ui.subtitle.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # build
        self.ui.layout = QHBoxLayout()
        self.ui.layout.setSpacing(12)
        self.ui.layout.addWidget(self.ui.cover)

        self.ui.inner_layout = QVBoxLayout()
        self.ui.inner_layout.setSpacing(0)
        self.ui.inner_layout.addWidget(self.ui.title)
        self.ui.inner_layout.addWidget(self.ui.subtitle)
        self.ui.layout.addLayout(self.ui.inner_layout)

        self.setLayout(self.ui.layout)

    def invalidate(self):
        self.result = repository.get_entity(self.result_id) # reload

        debug(f"Invalidating result {self.result.id}")

        pixmap = None
        if isinstance(self.result, ReleaseGroup):
            cover = self.result.images.preferred_image()
            pixmap = make_pixmap_from_data(cover, default=globals.COVER_PLACEHOLDER_PIXMAP)
        if isinstance(self.result, Artist):
            image = self.result.images.preferred_image()
            if image:
                debug("Artist has image")
            else:
                debug("Artist has no image")

            pixmap = make_pixmap_from_data(image, default=globals.PERSON_PLACEHOLDER_PIXMAP)

        title = None
        if isinstance(self.result, ReleaseGroup):
            title = self.result.title
        if isinstance(self.result, Artist):
            title = self.result.name

        subtitle = None
        if isinstance(self.result, ReleaseGroup):
            subtitle = self.result.artists_string()
        if isinstance(self.result, Artist):
            subtitle = "Artist"

        # pixmap
        if pixmap:
            self.ui.cover.setPixmap(pixmap)

        # title
        self.ui.title.setText(title)
        self.ui.title.setAlignment((Qt.AlignLeft | Qt.AlignBottom) if subtitle else (Qt.AlignLeft | Qt.AlignVCenter))


        # subtitle
        if subtitle:
            self.ui.subtitle.setText(subtitle)
        else:
            self.ui.subtitle.setVisible(False)

class SearchResultsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()
        self.results: List[str] = []

    def items(self) -> List:
        return self.results

class SearchResultsWidget(ListWidgetModelView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, item) -> ListWidgetModelViewItem:
        return SearchResultsItemWidget(item)