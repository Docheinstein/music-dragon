from typing import Optional, List, Any

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget

from log import debug


class ListWidgetModel:
    def __init__(self):
        pass

    def items(self) -> List:
        raise NotImplementedError("items() must be implemented by ListWidgetModel subclasses")

    def item_count(self) -> int:
        return len(self.items())

    def item(self, index: int) -> Optional[Any]:
        items = self.items()
        if 0 <= index < len(items):
            return items[index]
        return None

    def index(self, item: Any) -> Optional[int]:
        try:
            return self.items().index(item)
        except ValueError:
            pass
        return None

class ListWidgetModelViewItem(QWidget):
    def __init__(self):
        super().__init__()

    def setup(self):
        raise NotImplementedError("setup() must be implemented by ListWidgetModelViewItem subclasses")

    def invalidate(self):
        raise NotImplementedError("invalidate() must be implemented by ListWidgetModelViewItem subclasses")


class ListWidgetModelView(QListWidget):
    row_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model: Optional[ListWidgetModel] = None
        self.itemClicked.connect(self._on_item_clicked)

    def set_model(self, model: ListWidgetModel) -> None:
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
        debug(f"{type(self).__name__}.update_row({item})")
        item_index = self.model.index(item)
        if item_index is not None:
            self.update_row_at(item_index)

    def update_row_at(self, idx: int):
        debug(f"{type(self).__name__}.update_row_at({idx})")
        item = self.item(idx)
        widget: ListWidgetModelViewItem = self.itemWidget(item)
        widget.invalidate()

    def add_row(self, row_item):
        debug(f"{type(self).__name__}.add_row({row_item})")
        item = QListWidgetItem()
        widget = self.make_item_widget(row_item)
        item.setSizeHint(widget.sizeHint())

        self.addItem(item)
        self.setItemWidget(item, widget)

    def make_item_widget(self, item) -> ListWidgetModelViewItem:
        debug(f"{type(self).__name__}.make_item_widget({item})")
        raise NotImplementedError("make_item_widget() must be implemented by QListWidgetModelView subclasses")

    def _on_item_clicked(self, item: QListWidgetItem):
        debug(f"{type(self).__name__}.on_item_clicked at row {self.row(item)}")
        self.row_clicked.emit(self.row(item))