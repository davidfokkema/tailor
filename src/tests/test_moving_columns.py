import pandas as pd
from PySide6 import QtCore, QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 300)
        self.table_view = QtWidgets.QTableView()
        self.data_model = DataModel()
        self.setCentralWidget(self.table_view)

        self.table_view.setModel(self.data_model)
        self.header = self.table_view.horizontalHeader()
        self.header.setSectionsMovable(True)
        self.header.sectionMoved.connect(self.reset_column_ordering)

    def reset_column_ordering(self, logical, old_visual, new_visual):
        print(f"{logical=}, {old_visual=}, {new_visual=}")
        self.show_ordering()
        self.header.blockSignals(True)
        # move the column back, keep the header in logical order
        self.header.moveSection(new_visual, old_visual)
        self.header.blockSignals(False)
        # move the underlying data column instead
        self.data_model.moveColumn(None, old_visual, None, new_visual)
        self.show_ordering()

    def show_ordering(self):
        ordering = [self.header.logicalIndex(idx) for idx in range(self.header.count())]
        print(f"{ordering=}")


class DataModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data = pd.DataFrame({"x": 5 * [1], "y": 5 * [2], "z": 5 * [3]})

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._data.columns)

    def data(self, index, role):
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            return str(self._data.iat[index.row(), index.column()])
        else:
            return None

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return str(self._data.columns[section])
        else:
            return None

    def moveColumn(
        self, sourceParent, sourceColumn, destinationParent, destinationChild
    ):
        cols = list(self._data.columns)
        cols.insert(destinationChild, cols.pop(sourceColumn))
        self._data = self._data[cols]
        return True


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = MainWindow()

    app.show()
    qapp.exec()
