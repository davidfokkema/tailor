import numpy as np
import pandas as pd
import asteval

from PyQt5 import QtCore, QtGui


class DataModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()

        # FIXME: test data
        x = np.linspace(0, 10, 11)
        y = np.random.normal(loc=x, scale=0.1 * x, size=len(x))
        self._data = pd.DataFrame.from_dict(
            {"U": x, "I": y, "dU": 0.1 * x + 0.01, "dI": 0.1 * y + 0.01}
        )

        self._calculated_columns = {}

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if role == QtCore.Qt.DisplayRole:
            return float(self._data.iat[row, col])
        elif role == QtCore.Qt.BackgroundRole:
            if self.get_column_name(col) in self._calculated_columns:
                return QtGui.QBrush(QtGui.QColor(255, 255, 200))
        return QtCore.QVariant()

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            try:
                self._data.iat[row, col] = value
            except ValueError:
                return False
            else:
                return True
        return False

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._data.columns[section]
            else:
                return self._data.index[section]
        return QtCore.QVariant()

    def insertColumn(self, column, parent=None):
        column_name = "y" + str(column)

        self.beginInsertColumns(QtCore.QModelIndex(), column, column)
        self._data.insert(column, column_name, np.nan)
        self.endInsertColumns()

        self._calculated_columns[column_name] = None

    def rename_column(self, col_idx, new_name):
        old_name = self._data.columns[col_idx]
        self._data.rename(columns={old_name: new_name}, inplace=True)
        try:
            self._calculated_columns[new_name] = self._calculated_columns.pop(old_name)
        except KeyError:
            pass
        self.headerDataChanged.emit(QtCore.Qt.Horizontal, col_idx, col_idx)

    def recalculate_column(self, col_idx, expression):
        col_name = self.get_column_name(col_idx)
        if col_name in self._calculated_columns:
            objects = {
                k: self._data[k] for k in self._data.columns if k is not col_name
            }
            try:
                aeval = asteval.Interpreter(usersyms=objects)
                output = aeval(expression)
            except NameError:
                pass
            else:
                self._calculated_columns[col_name] = expression
                self._data[col_name] = output
                top_left = self.createIndex(0, col_idx)
                bottom_right = self.createIndex(len(self._data), col_idx)
                self.dataChanged.emit(top_left, bottom_right)

    def flags(self, index):
        flags = super().flags(index)
        return flags | QtCore.Qt.ItemIsEditable

    def get_column_name(self, idx):
        return self._data.columns[idx]

    def get_column_names(self):
        return list(self._data.columns)

    def get_column_expression(self, idx):
        col_name = self.get_column_name(idx)
        try:
            return self._calculated_columns[col_name]
        except KeyError:
            return None

    def get_column(self, col_name):
        return self._data[col_name]

    def get_columns(self, col_names):
        return [self._data[c] for c in col_names]
