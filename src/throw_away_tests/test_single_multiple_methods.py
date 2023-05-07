"""Test default implementation of singular insertColumn.

The singular methods insertColumn, insertRow, removeColumn and removeRow call
the plural methods *Columns and *Rows. Therefore, only the plural methods need
to be implemented by subclasses.

"""

from PySide6 import QtCore
from PySide6.QtCore import QModelIndex, QPersistentModelIndex


class TableModel(QtCore.QAbstractTableModel):
    def insertColumns(
        self, column: int, count: int, parent: QModelIndex | QPersistentModelIndex = ...
    ) -> bool:
        print(
            f"insertColumns called with {column=}, {count=}, {parent=} ({parent.isValid()=})"
        )
        return super().insertColumns(column, count, parent)


if __name__ == "__main__":
    model = TableModel()
    model.insertColumn(0)
