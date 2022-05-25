from typing import Optional, List, Any

from PyQt5.QtCore import pyqtSignal, QCoreApplication
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QApplication

from log import debug


class ListWidgetModel:
    def __init__(self):
        pass

    def entries(self) -> List:
        raise NotImplementedError("items() must be implemented by ListWidgetModel subclasses")

    def entry_count(self) -> int:
        return len(self.entries())

    def entry(self, index: int) -> Optional[Any]:
        items = self.entries()
        if 0 <= index < len(items):
            return items[index]
        return None

    def index(self, entry: Any) -> Optional[int]:
        try:
            return self.entries().index(entry)
        except ValueError:
            pass
        return None

class ListWidgetModelViewItem(QWidget):
    def __init__(self, entry: Any):
        super().__init__()
        self.entry = entry

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
        self.setUniformItemSizes(True)

    def set_model(self, model: ListWidgetModel) -> None:
        self.model = model
        self.invalidate()

    def clear(self) -> None:
        debug(f"{type(self).__name__}.clear()")
        super().clear()

    def invalidate(self):
        self.clear()
        debug(f"{type(self).__name__}.invalidate()")
        entry_count = self.model.entry_count()
        if not entry_count:
            debug(f"{type(self).__name__}.invalidate(): nothing to do")
            return
        debug(f"{type(self).__name__}.invalidate(): adding {entry_count} rows")
        for entry in self.model.entries():
            self.add_row(entry)

    def update_row(self, entry: Any):
        debug(f"{type(self).__name__}.update_row({entry})")
        entry_index = self.model.index(entry)
        if entry_index is not None:
            self.update_row_at(entry_index)

    def update_row_at(self, idx: int):
        debug(f"{type(self).__name__}.update_row_at({idx})")
        item = self.item(idx)
        widget: ListWidgetModelViewItem = self.itemWidget(item)
        widget.invalidate()

    def add_row(self, entry: Any):
        debug(f"{type(self).__name__}.add_row({entry})")
        item = QListWidgetItem()
        widget = self.make_item_widget(entry)
        item.setSizeHint(widget.sizeHint())

        self.addItem(item)
        self.setItemWidget(item, widget)

    def make_item_widget(self, entry) -> ListWidgetModelViewItem:
        debug(f"{type(self).__name__}.make_item_widget({entry})")
        raise NotImplementedError("make_item_widget() must be implemented by QListWidgetModelView subclasses")

    def _on_item_clicked(self, item: QListWidgetItem):
        debug(f"{type(self).__name__}.on_item_clicked at row {self.row(item)}")
        self.row_clicked.emit(self.row(item))