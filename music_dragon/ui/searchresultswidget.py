from typing import Optional, List

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout, QListWidgetItem, QSpacerItem

from music_dragon.ui import resources
from music_dragon.repository import get_entity, Track
from music_dragon.log import debug
from music_dragon.repository import Artist, ReleaseGroup
from music_dragon.ui.clickablelabel import ClickableLabel
from music_dragon.ui.listwidgetmodelview import ListWidgetModelViewItem, ListWidgetModel, ListWidgetModelView
from music_dragon.utils import make_pixmap_from_data


class SearchResultsItemWidget(ListWidgetModelViewItem):
    subtitle_first_clicked = pyqtSignal(str)
    subtitle_second_clicked = pyqtSignal(str)

    class Ui:
        def __init__(self):
            self.cover: Optional[QLabel] = None
            self.title: Optional[QLabel] = None
            self.subtitle_first: Optional[ClickableLabel] = None
            self.subtitle_sep: Optional[QLabel] = None
            self.subtitle_second: Optional[ClickableLabel] = None

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
        self.ui.cover.setMaximumSize(QSize(64, 64))
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
        self.ui.subtitle.clicked.connect(self._on_subtitle_first_clicked)
        self.ui.subtitle.set_underline_on_hover(True)

        # subtitle first
        self.ui.subtitle_first = ClickableLabel()
        self.ui.subtitle_first.set_underline_on_hover(True)
        f = self.ui.subtitle_first.font()
        f.setPointSize(10)
        self.ui.subtitle_first.setFont(f)
        self.ui.subtitle_first.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ui.subtitle_first.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.ui.subtitle_first.clicked.connect(self._on_subtitle_first_clicked)

        # -
        self.ui.subtitle_sep = QLabel(" - ")
        f = self.ui.subtitle_sep.font()
        f.setPointSize(10)
        self.ui.subtitle_sep.setFont(f)
        self.ui.subtitle_sep.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ui.subtitle_sep.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # subtitle second
        self.ui.subtitle_second = ClickableLabel()
        self.ui.subtitle_second.set_underline_on_hover(True)
        f = self.ui.subtitle_second.font()
        f.setPointSize(10)
        self.ui.subtitle_second.setFont(f)
        self.ui.subtitle_second.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ui.subtitle_second.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.ui.subtitle_second.clicked.connect(self._on_subtitle_second_clicked)

        # build
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(self.ui.cover)

        inner_layout = QVBoxLayout()

        subtitle_layout = QHBoxLayout()
        subtitle_layout.addWidget(self.ui.subtitle_first)
        subtitle_layout.addWidget(self.ui.subtitle_sep)
        subtitle_layout.addWidget(self.ui.subtitle_second)
        subtitle_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        inner_layout.setSpacing(0)
        inner_layout.addWidget(self.ui.title)
        inner_layout.addLayout(subtitle_layout)

        layout.addLayout(inner_layout)

        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.setLayout(layout)

    def invalidate(self):
        if self.result_id is None:
            return

        self.result = get_entity(self.result_id)

        debug(f"Invalidating result {self.result.id}")

        pixmap = None
        if isinstance(self.result, ReleaseGroup):
            cover = self.result.preferred_front_cover()
            pixmap = make_pixmap_from_data(cover, default=resources.COVER_PLACEHOLDER_PIXMAP)
        elif isinstance(self.result, Artist):
            image = self.result.image
            pixmap = make_pixmap_from_data(image, default=resources.PERSON_PLACEHOLDER_PIXMAP)
        elif isinstance(self.result, Track):
            if self.result.release():
                # debug(f"Found cover for track {self.result.id}")
                image = self.result.release().release_group().preferred_front_cover()
            else:
                # debug(f"No cover found for track {self.result.id}")
                image = None # hack
            pixmap = make_pixmap_from_data(image, default=resources.COVER_PLACEHOLDER_PIXMAP)

        title = None
        if isinstance(self.result, ReleaseGroup):
            title = self.result.title
        elif isinstance(self.result, Artist):
            title = self.result.name
        elif isinstance(self.result, Track):
            title = self.result.title

        subtitle_first = None
        subtitle_second = None
        subtitle_first_clickable = False
        subtitle_second_clickable = False

        if isinstance(self.result, ReleaseGroup):
            subtitle_first = self.result.artists_string()
            subtitle_first_clickable = True
            self.ui.subtitle_first.set_clickable(False)

        elif isinstance(self.result, Artist):
            subtitle_first = "Artist"
            subtitle_first_clickable = False
        elif isinstance(self.result, Track):
            if self.result.release():
                subtitle_first = self.result.release().release_group().artists_string()
                subtitle_second = self.result.release().release_group().title
            subtitle_first_clickable = True
            subtitle_second_clickable = True

        # pixmap
        if pixmap:
            self.ui.cover.setPixmap(pixmap)

        # title
        self.ui.title.setText(title)
        self.ui.title.setAlignment((Qt.AlignLeft | Qt.AlignBottom) if (subtitle_first or subtitle_second) else (Qt.AlignLeft | Qt.AlignVCenter))

        # subtitle
        if subtitle_first:
            self.ui.subtitle_first.setText(subtitle_first)
        else:
            self.ui.subtitle_first.setVisible(False)
        self.ui.subtitle_first.set_clickable(subtitle_first_clickable)
        self.ui.subtitle_first.set_underline_on_hover(subtitle_first_clickable)


        if subtitle_second:
            self.ui.subtitle_second.setText(subtitle_second)
        else:
            self.ui.subtitle_second.setVisible(False)
        self.ui.subtitle_second.set_clickable(subtitle_second_clickable)
        self.ui.subtitle_second.set_underline_on_hover(subtitle_second_clickable)


        self.ui.subtitle_sep.setVisible(True if (subtitle_first and subtitle_second) else False)


    def _on_subtitle_first_clicked(self, ev: QMouseEvent):
        debug(f"_on_subtitle_first_clicked({self.entry})")
        ev.accept() # prevent propagation
        self.subtitle_first_clicked.emit(self.entry)

    def _on_subtitle_second_clicked(self, ev: QMouseEvent):
        debug(f"_on_subtitle_second_clicked({self.entry})")
        ev.accept() # prevent propagation
        self.subtitle_second_clicked.emit(self.entry)

class SearchResultsModel(ListWidgetModel):
    def __init__(self):
        super().__init__()
        self.results: List[str] = []

    def entries(self) -> List:
        return self.results

class SearchResultsWidget(ListWidgetModelView):
    subtitle_first_clicked = pyqtSignal(int)
    subtitle_second_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        w = SearchResultsItemWidget(entry)
        w.subtitle_first_clicked.connect(self._on_subtitle_first_clicked)
        w.subtitle_second_clicked.connect(self._on_subtitle_second_clicked)
        return w

    def _on_subtitle_first_clicked(self, entry: str):
        row = self.model.index(entry)
        self.subtitle_first_clicked.emit(row)

    def _on_subtitle_second_clicked(self, entry: str):
        row = self.model.index(entry)
        self.subtitle_second_clicked.emit(row)