from typing import Optional, List

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout, QListWidgetItem, QSpacerItem

import ui
from repository import get_entity
from log import debug
from repository import Artist, ReleaseGroup
from ui.clickablelabel import ClickableLabel
from ui.listwidgetmodelview import ListWidgetModelViewItem, ListWidgetModel, ListWidgetModelView
from utils import make_pixmap_from_data


class SearchResultsItemWidget(ListWidgetModelViewItem):
    subtitle_clicked = pyqtSignal(str)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.subtitle: Optional[ClickableLabel] = None
            self.layout = None
            self.inner_layout = None

    def __init__(self, item_id):
        super().__init__(entry=item_id)
        self.result_id = item_id
        self.result = get_entity(self.result_id)
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
        font = self.ui.title.font()
        font.setBold(True)
        font.setPointSize(14)
        self.ui.title.setFont(font)

        # subtitle
        self.ui.subtitle = ClickableLabel()
        self.ui.subtitle.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.ui.subtitle.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ui.subtitle.clicked.connect(self._on_subtitle_clicked)
        self.ui.subtitle.set_underline_on_hover(True)

        # build
        self.ui.layout = QHBoxLayout()
        self.ui.layout.setSpacing(12)
        self.ui.layout.addWidget(self.ui.cover)

        self.ui.inner_layout = QVBoxLayout()
        self.ui.inner_layout.setSpacing(0)
        self.ui.inner_layout.addWidget(self.ui.title)
        self.ui.inner_layout.addWidget(self.ui.subtitle)

        self.ui.layout.addLayout(self.ui.inner_layout)

        self.ui.layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.setLayout(self.ui.layout)

    def invalidate(self):
        if self.result_id is None:
            return

        self.result = get_entity(self.result_id)

        debug(f"Invalidating result {self.result.id}")

        pixmap = None
        if isinstance(self.result, ReleaseGroup):
            cover = self.result.images.preferred_image()
            pixmap = make_pixmap_from_data(cover, default=ui.resources.COVER_PLACEHOLDER_PIXMAP)
        if isinstance(self.result, Artist):
            image = self.result.images.preferred_image()
            if image:
                debug("Artist has image")
            else:
                debug("Artist has no image")

            pixmap = make_pixmap_from_data(image, default=ui.resources.PERSON_PLACEHOLDER_PIXMAP)

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
            self.ui.subtitle.set_clickable(False)

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

    def _on_subtitle_clicked(self, ev: QMouseEvent):
        debug(f"on_subtitle_clicked({self.result_id})")
        ev.accept() # prevent propagation
        self.subtitle_clicked.emit(self.result_id)

class SearchResultsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()
        self.results: List[str] = []

    def entries(self) -> List:
        return self.results

class SearchResultsWidget(ListWidgetModelView):
    subtitle_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        w = SearchResultsItemWidget(entry)
        w.subtitle_clicked.connect(self._on_subtitle_clicked)
        return w

    def _on_subtitle_clicked(self, entry: str):
        row = self.model.index(entry)
        self.subtitle_clicked.emit(row)