from PyQt5.QtCore import QModelIndex, QSortFilterProxyModel
from PyQt5.QtWidgets import QListView


class ListProxyView(QListView):
    def _source_index(self, idx: QModelIndex):
        m = self.model()
        try:
            return m.mapToSource(idx)
        except:
            return idx