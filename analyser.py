import sys

import numpy as np
import pandas as pd
from PyQt5 import uic, QtCore, QtWidgets


class UserInterface(QtWidgets.QMainWindow):
    def __init__(self):
        # roep de __init__() aan van de parent class
        super().__init__()

        uic.loadUi(open("analyser.ui"), self)

        data_model = DataModel()
        self.data_view.setModel(data_model)


class DataModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()

        x = np.linspace(0, 10, 11)
        y = x ** 2
        self._data = pd.DataFrame.from_dict({"x": x, "y": y})
        pass

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._data.columns)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            col = index.column()
            return float(self._data.iat[row, col])
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

    def flags(self, index):
        flags = super().flags(index)
        return flags | QtCore.Qt.ItemIsEditable


def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = UserInterface()
    ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
