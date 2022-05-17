from typing import Optional, List, Any

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget

from log import debug


class QListWidgetModel:
    def __init__(self):
        pass

    def item_count(self) -> int:
        raise NotImplementedError("item_count() must be implemented by QListWidgetModel subclasses")

    def item(self, index: int) -> Optional[Any]:
        raise NotImplementedError("item() must be implemented by QListWidgetModel subclasses")

    def index(self, item: Any) -> Optional[int]:
        raise NotImplementedError("index() must be implemented by QListWidgetModel subclasses")

    def items(self) -> List:
        raise NotImplementedError("items() must be implemented by QListWidgetModel subclasses")


class QListWidgetModelViewItem(QWidget):
    def __init__(self):
        super().__init__()

    def setup(self):
        raise NotImplementedError("setup() must be implemented by QListWidgetModelViewItem subclasses")

    def invalidate(self):
        raise NotImplementedError("invalidate() must be implemented by QListWidgetModelViewItem subclasses")


class QListWidgetModelView(QListWidget):
    row_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model: Optional[QListWidgetModel] = None
        self.itemClicked.connect(self._on_item_clicked)

    def set_model(self, model: QListWidgetModel) -> None:
        self.model = model
        self.invalidate()

    def invalidate(self):
        self.clear()
        debug(f"{type(self).__name__}.invalidate()")
        item_count = self.model.item_count()
        if not item_count:
            debug(f"{type(self).__name__}.invalidate(): nothing to do")
            return
        debug(f"{type(self).__name__}.invalidate(): adding {item_count} rows")
        for item in self.model.items():
            self.add_row(item)


    def update_row(self, item: Any):
        item_index = self.model.index(item)
        if item_index is not None:
            self.update_row_at(item_index)

    def update_row_at(self, idx: int):
        item = self.item(idx)
        widget: QListWidgetModelViewItem = self.itemWidget(item)
        widget.invalidate()

    def add_row(self, item):
        item = QListWidgetItem()
        widget = self.make_item_widget(item)
        item.setSizeHint(widget.sizeHint())

        self.addItem(item)
        self.setItemWidget(item, widget)

    def make_item_widget(self, item) -> QListWidgetModelViewItem:
        raise NotImplementedError("make_item_widget() must be implemented by QListWidgetModelView subclasses")

    def _on_item_clicked(self, item: QListWidgetItem):
        debug(f"on_item_clicked at row {self.row(item)}")
        self.row_clicked.emit(self.row(item))