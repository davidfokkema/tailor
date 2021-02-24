"""Data model for the analyser app.

Implements a QAbstractDataModel to contain the data values as a backend for the
table view used in the app.
"""

import numpy as np
import pandas as pd
import asteval

from PyQt5 import QtCore, QtGui


class DataModel(QtCore.QAbstractTableModel):
    """Data model for the analyser app.

    Implements a QAbstractDataModel to contain the data values as a backend for the
    table view used in the app.
    """

    _new_col_num = 0

    def __init__(self):
        """Instantiate the class."""
        super().__init__()

        # FIXME: test data
        # x = np.linspace(0, 10, 11)
        # y = np.random.normal(loc=x, scale=0.1 * x, size=len(x))
        # self._data = pd.DataFrame.from_dict(
        #     {"U": x, "I": y, "dU": 0.1 * x + 0.01, "dI": 0.1 * y + 0.01}
        # )
        self._data = pd.DataFrame.from_dict({"x": [np.nan], "y": [np.nan]})

        self._calculated_columns = {}

    def rowCount(self, parent=None):
        """Return the number of rows in the data."""
        return len(self._data)

    def columnCount(self, parent=None):
        """Return the number of columns in the data."""
        return len(self._data.columns)

    def data(self, index, role):
        """Return (attributes of) the data.

        This method is called by the table view to request data points or its
        attributes. For each table cell multiple calls are made, one for each
        'role'. The role indicates the type of data that is requested. For
        example, the DisplayRole indicates a string is requested to display in
        the cell. Also, a BackgroundRole indicates that the background color for
        the cell is requested. You can use this to indicate different types of
        data, e.g. calculated or input data.

        If a role is requested that is not implemented an invalid QVariant is
        returned.

        Args:
            index: a QModelIndex referencing the requested data item.
            role: an ItemDataRole to indicate what type of information is
                requested.

        Returns: The requested data or an invalid QVariant.
        """
        row = index.row()
        col = index.column()

        if role == QtCore.Qt.DisplayRole:
            # request for the data itself
            value = float(self._data.iat[row, col])
            if np.isnan(value) and not self.is_calculated_column(col):
                # NaN in a data column, show as empty
                return ""
            else:
                return value
        elif role == QtCore.Qt.BackgroundRole:
            # request for the background fill of the cell
            if self.is_calculated_column(col):
                return QtGui.QBrush(QtGui.QColor(255, 255, 200))
        # not implemented, return an invalid QVariant per the docs
        return QtCore.QVariant()

    def setData(self, index, value, role):
        """Set (attributes of) data values.

        This method is used to set data values in the model. The role indicates
        the type of data to set. Currently, only the EditRole is supported for
        setting values through the table view's cell editing machinery.

        Args:
            index: a QModelIndex referencing the requested data item.
            value: the value to set.
            role: an ItemDataRole to indicate what type of information is
                requested.
        
        Returns:
            True if the data could be set. False otherwise.
        """
        # FIXME: a dataChanged signal should be emitted?
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            try:
                self._data.iat[row, col] = value
            except ValueError:
                return False
            else:
                return True
        # Role not implemented
        return False

    def headerData(self, section, orientation, role):
        """Return row and column information.

        Return data on the row and column headers. Mainly useful for displaying
        the names of the columns and the row numbers in the table view. The
        orientation should be specified as Qt.Horizontal for column headers and
        Qt.Vertical for row headers. The role should specify what type of data is requested.

        Args:
            section: an integer section (row or column) number.
            orientation: the orientation of the header.
            role: an ItemDataRole to indicate what type of information is
                requested.

        Returns:
            The data, if available, or an invalid QVariant.
        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._data.columns[section]
            else:
                return str(self._data.index[section])
        return QtCore.QVariant()

    def insertColumn(self, column, parent=None, column_name=None):
        """Insert a single column.

        Insert a column *before* the specified column number. Returns True if
        the insertion was succesful.

        Args:
            column: an integer column number to indicate the place of insertion.
            parent: a QModelIndex pointing to the model (ignored).

        Returns:
            True if the insertion was succesful, False otherwise.
        """
        if column_name is None:
            column_name = self._create_new_column_name()

        self.beginInsertColumns(QtCore.QModelIndex(), column, column)
        self._data.insert(column, column_name, np.nan)
        self.endInsertColumns()
        return True

    def removeColumn(self, column, parent=None):
        """Remove a single column.

        Removes a column at the specified column number. Returns True if the
        removal was succesful.

        Args:
            column: an integer column number to indicate the place of removal.
            parent: a QModelIndex pointing to the model (ignored).

        Returns:
            True if the removal was succesful, False otherwise.
        """
        column_name = self.get_column_name(column)
        self.beginRemoveColumns(QtCore.QModelIndex(), column, column)
        self._data.drop(column_name, axis=1, inplace=True)
        self.endRemoveColumns()
        return True

    def removeRow(self, row, parent=None):
        """Remove a single row.

        Removes a row at the specified row number. Returns True if the
        removal was succesful.

        Args:
            row: an integer row number to indicate the place of removal.
            parent: a QModelIndex pointing to the model (ignored).

        Returns:
            True if the removal was succesful, False otherwise.
        """
        index = self._data.index[row]
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        self._data.drop(index, axis=0, inplace=True)
        self._data.reset_index(drop=True, inplace=True)
        self.endRemoveRows()
        return True

    def insertRow(self, row, parent=None):
        """Insert a single row.

        Append a row to the table, ignoring the specified row number. Returns
        True if the insertion was succesful.

        Args:
            row: an integer row number to indicate the place of insertion
                (ignored).
            parent: a QModelIndex pointing to the model (ignored).

        Returns:
            True if the insertion was succesful, False otherwise.
        """
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        num_col = len(self._data.columns)
        self._data.loc[row] = num_col * [np.nan]
        self.endInsertRows()
        return True

    def insert_calculated_column(self, column):
        """Insert a calculated column.

        Insert a column *before* the specified column number. Returns True if
        the insertion was succesful.

        Args:
            column: an integer column number to indicate the place of insertion.

        Returns:
            True if the insertion was succesful, False otherwise.
        """
        column_name = self._create_new_column_name()

        if self.insertColumn(column, column_name=column_name) is True:
            self._calculated_columns[column_name] = None
            return True
        else:
            return False

    def rename_column(self, col_idx, new_name):
        """Rename a column.

        Renames the column at the specified index.

        Args:
            col_idx: an integer column number.
            new_name: a string with the new column name.
        """
        old_name = self._data.columns[col_idx]
        self._data.rename(columns={old_name: new_name}, inplace=True)
        try:
            self._calculated_columns[new_name] = self._calculated_columns.pop(old_name)
        except KeyError:
            pass
        self.headerDataChanged.emit(QtCore.Qt.Horizontal, col_idx, col_idx)

    def recalculate_column(self, col_idx, expression):
        """Recalculate column values.

        Calculate column values bases on some mathematical expression.

        Args:
            col_idx: an integer column number.
            expression: a string with a mathematical expression used to
                calculate the column values.
        """
        col_name = self.get_column_name(col_idx)
        if self.is_calculated_column(col_idx):
            objects = {
                k: self._data[k] for k in self._data.columns if k is not col_name
            }
            aeval = asteval.Interpreter(usersyms=objects)
            output = aeval(expression)
            if aeval.error:
                for err in aeval.error:
                    exc, msg = err.get_error()
                    print(f"Evaluation of mathematical expression raised {exc}: {msg}")
            elif output is not None:
                self._calculated_columns[col_name] = expression
                self._data[col_name] = output
                top_left = self.createIndex(0, col_idx)
                bottom_right = self.createIndex(len(self._data), col_idx)
                self.dataChanged.emit(top_left, bottom_right)
            else:
                print("No evaluation error but no output.")

    def flags(self, index):
        """Returns item flags.

        Returns the item flags for the given index.

        Args:
            index: a QModelIndex referencing the requested data item.

        Returns:
            The requested flags.
        """
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        col = index.column()
        if not self.is_calculated_column(col):
            # You can only edit data if the column values are not calculated
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def get_column_name(self, col_idx):
        """Get column name.

        Get column name at the given index.

        Args:
            col_idx: an integer column number.

        Returns:
            The column name as a string.
        """
        return self._data.columns[col_idx]

    def get_column_names(self):
        """Get list of all column names."""
        return list(self._data.columns)

    def get_column_expression(self, col_idx):
        """Get column expression.

        Get the mathematical expression used to calculate values in the column
        at the given index.

        Args:
            col_idx: an integer column number.

        Returns:
            A string containing the mathematical expression or None.
        """
        col_name = self.get_column_name(col_idx)
        try:
            return self._calculated_columns[col_name]
        except KeyError:
            return None

    def get_column(self, col_name):
        """Return column values.

        Args:
            col_name: a string containing the column name.

        Returns:
            A pandas.Series containing the column values.
        """
        return self._data[col_name]

    def get_columns(self, col_names):
        """Return values for multiple columns.

        Args:
            col_names: a list of strings containing the column names.

        Returns:
            A list of pandas.Series containing the column values.
        """
        return [self._data[c] for c in col_names]

    def is_calculated_column(self, col_idx=None, col_name=None):
        """Check if column is calculated.

        Supplied with either a column index or a column name (index takes precedence), checks whether the column is calculated from a mathematical expression.

        Args:
            col_idx: an integer column index (takes precedence over name).
            col_name: a string containing the column name.

        Returns:
            True if the column is calculated, False otherwise.
        """
        if col_idx is not None:
            col_name = self.get_column_name(col_idx)
        return col_name in self._calculated_columns

    def _create_new_column_name(self):
        """Create a name for a new column.

        Creates column names like new1, new2, etc. while making sure the new
        name is not yet taken.

        Returns:
            A string containing the new name.
        """
        col_names = self.get_column_names()
        while True:
            self._new_col_num += 1
            new_name = f"new{self._new_col_num}"
            if new_name not in col_names:
                return new_name
