import sys

import numpy as np
import pandas as pd
from PyQt5 import uic, QtCore, QtGui, QtWidgets

import pyqtgraph as pg


pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class UserInterface(QtWidgets.QMainWindow):

    _selected_col_idx = None

    def __init__(self):
        # roep de __init__() aan van de parent class
        super().__init__()

        uic.loadUi(open("analyser.ui"), self)

        self.data_model = DataModel()
        self.data_view.setModel(self.data_model)

        self.selection = self.data_view.selectionModel()
        self.selection.selectionChanged.connect(self.selection_changed)

        self.add_column_button.clicked.connect(self.add_column)
        self.name_edit.textEdited.connect(self.rename_column)
        self.recalculate_button.clicked.connect(self.recalculate_column)
        self.create_plot_button.clicked.connect(self.create_plot_dialog)

        # self.create_plot("U", "I", "dU", "dI")

    def selection_changed(self, selected, deselected):
        if not selected.isEmpty():
            first_selection = selected.first()
            col_idx = first_selection.left()
            self._selected_col_idx = col_idx
            self.name_edit.setText(self.data_model.get_column_name(col_idx))
            self.formula_edit.setText(self.data_model.get_column_expression(col_idx))

    def add_column(self):
        self.data_model.insertColumn(self.data_model.columnCount())

    def rename_column(self, name):
        if self._selected_col_idx is not None:
            self.data_model.rename_column(self._selected_col_idx, name)

    def recalculate_column(self):
        if self._selected_col_idx is not None:
            self.data_model.recalculate_column(
                self._selected_col_idx, self.formula_edit.text()
            )

    def create_plot_dialog(self):
        create_dialog = QtWidgets.QDialog(parent=self)
        uic.loadUi("create_plot_dialog.ui", create_dialog)
        choices = [None] + self.data_model.get_column_names()
        create_dialog.x_axis_box.addItems(choices)
        create_dialog.y_axis_box.addItems(choices)
        create_dialog.x_err_box.addItems(choices)
        create_dialog.y_err_box.addItems(choices)

        if create_dialog.exec() == QtWidgets.QDialog.Accepted:
            x_var = create_dialog.x_axis_box.currentText()
            y_var = create_dialog.y_axis_box.currentText()
            x_err = create_dialog.x_err_box.currentText()
            y_err = create_dialog.y_err_box.currentText()
            if x_var and y_var:
                self.create_plot(x_var, y_var, x_err, y_err)

    def create_plot(self, x_var, y_var, x_err, y_err):
        tab_count = self.tabWidget.count()
        plot_tab = QtWidgets.QWidget()
        uic.loadUi("plot_tab.ui", plot_tab)
        self.tabWidget.addTab(plot_tab, f"Plot {tab_count}")
        x = self.data_model._data[x_var]
        y = self.data_model._data[y_var]
        if x_err:
            width = 2 * self.data_model._data[x_err]
        else:
            width = None
        if y_err:
            height = 2 * self.data_model._data[y_err]
        else:
            height = None
        plot_tab.plot_widget.plot(
            x, y, symbol="o", pen=None, symbolSize=5, symbolPen="k", symbolBrush="k",
        )
        error_bars = pg.ErrorBarItem(x=x, y=y, width=width, height=height)
        plot_tab.plot_widget.addItem(error_bars)


class DataModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()

        x = np.linspace(0, 10, 11)
        y = np.random.normal(loc=x, scale=0.1 * x, size=len(x))
        self._data = pd.DataFrame.from_dict({"U": x, "I": y})

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
                output = eval(expression, {"__builtins__": {}}, objects)
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


def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = UserInterface()
    ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
