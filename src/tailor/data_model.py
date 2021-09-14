"""Data model for the tailor app.

Implements a QAbstractDataModel to contain the data values as a backend for the
table view used in the app.
"""
import re

import numpy as np
import pandas as pd
import asteval

from PyQt5 import QtCore, QtGui


# treat Inf and -Inf as missing values (e.g. when calling dropna())
pd.options.mode.use_inf_as_na = True


MSG_TIMEOUT = 0


class DataModel(QtCore.QAbstractTableModel):
    """Data model for the tailor app.

    Implements a QAbstractDataModel to contain the data values as a backend for the
    table view used in the app.
    """

    _new_col_num = 0
    _data = None
    _calculated_columns = None

    def __init__(self, main_window):
        """Instantiate the class."""
        super().__init__()

        self.main_window = main_window

        self._data = pd.DataFrame.from_dict({"x": 5 * [np.nan], "y": 5 * [np.nan]})
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

        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            # request for the data itself
            value = float(self._data.iat[row, col])
            if np.isnan(value) and not self.is_calculated_column(col):
                # NaN in a data column, show as empty
                return ""
            else:
                return f"{value:.10g}"
        elif role == QtCore.Qt.BackgroundRole:
            # request for the background fill of the cell
            if self.is_calculated_column(col):
                return QtGui.QBrush(QtGui.QColor(255, 255, 200))
        # not implemented, return an invalid QVariant per the docs
        return QtCore.QVariant()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
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
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            try:
                self._data.iat[row, col] = value
            except ValueError:
                self._data.iat[row, col] = np.nan
            finally:
                # FIXME: data changed, recalculate all columns; better to only
                # recalculate the current row
                self.recalculate_all_columns()
            self.dataChanged.emit(index, index)
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
                return str(self._data.index[section] + 1)
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
        try:
            del self._calculated_columns[column_name]
        except KeyError:
            # not a calculated column
            pass
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
        self.main_window.statusbar.showMessage("Renamed column.", msecs=MSG_TIMEOUT)

    def update_column_expression(self, col_idx, expression):
        """Update a calculated column with a new expression.

        Args:
            col_idx: an integer column number.
            expression: a string with a mathematical expression used to
                calculate the column values.
        """
        col_name = self.get_column_name(col_idx)
        if self.is_calculated_column(col_idx):
            if self.recalculate_column(col_name, expression):
                # calculation was successful
                self._calculated_columns[col_name] = expression
                top_left = self.createIndex(0, col_idx)
                bottom_right = self.createIndex(len(self._data), col_idx)
                self.dataChanged.emit(top_left, bottom_right)
                self.main_window.statusbar.showMessage(
                    "Updated column values.", msecs=MSG_TIMEOUT
                )

    def recalculate_column(self, col_name, expression=None):
        """Recalculate column values.

        Calculate column values based on its expression.

        Args:
            col_name: a string containing the column name.
            expression: an optional string that contains the mathematical
                expression. If None (the default) the expression is taken from the
                column information.

        Returns:
            True if the calculation was successful, False otherwise.
        """
        if expression is None:
            expression = self._calculated_columns[col_name]
        objects = {k: self._data[k] for k in self._data.columns if k is not col_name}
        aeval = asteval.Interpreter(usersyms=objects)
        output = aeval(expression)
        if aeval.error:
            for err in aeval.error:
                exc, msg = err.get_error()
                self.main_window.statusbar.showMessage(
                    f"ERROR: {exc}: {msg}.", msecs=MSG_TIMEOUT
                )
        elif output is not None:
            if isinstance(output, pd.Series):
                output = output.astype("float64")
            else:
                output = float(output)
            self._data[col_name] = output
            return True
        else:
            print(f"No evaluation error but no output for expression {expression}.")
        return False

    def recalculate_all_columns(self):
        """Recalculate all columns.

        If data is entered or changed, the calculated column values must be
        updated. This method will manually recalculate all column values.
        """
        self.beginResetModel()
        for col_name in self._calculated_columns:
            self.recalculate_column(col_name)
        self.endResetModel()

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

    def save_state_to_obj(self, save_obj):
        """Save all data and state to save object.

        Args:
            save_obj: a dictionary to store the data and state.
        """
        save_obj.update(
            {
                "data": self._data.to_dict("list"),
                "calculated_columns": self._calculated_columns,
                "new_col_num": self._new_col_num,
            }
        )

    def load_state_from_obj(self, save_obj):
        """Load all data and state from save object.

        Args:
            save_obj: a dictionary that contains the saved data and state.
        """
        self.beginResetModel()
        self._data = pd.DataFrame.from_dict(save_obj["data"])
        self._calculated_columns = save_obj["calculated_columns"]
        self._new_col_num = save_obj["new_col_num"]
        self.endResetModel()

    def write_csv(self, filename):
        """Write all data to CSV file.

        Args:
            filename: a string containing the full filename.
        """
        self._data.to_csv(filename, index=False)

    def read_csv(
        self,
        filename,
        delimiter=None,
        decimal=".",
        thousands=",",
        header=None,
        skiprows=0,
    ):
        """Read data from CSV file.

        Overwrites all existing data by importing a CSV file.

        Args:
            filename: a string containing the path to the CSV file
            delimiter: a string containing the column delimiter
            decimal: a string containing the decimal separator
            thousands: a string containing the thousands separator
            header: an integer with the row number containing the column names,
                or None.
            skiprows: an integer with the number of rows to skip at start of file
        """
        self.beginResetModel()

        self._data = self._read_csv_into_dataframe(
            filename, delimiter, decimal, thousands, header, skiprows
        )
        self._calculated_columns = {}

        self.endResetModel()

    def read_and_concat_csv(
        self,
        filename,
        delimiter=None,
        decimal=".",
        thousands=",",
        header=None,
        skiprows=0,
    ):
        """Read data from CSV file and concatenate with current data.

        Overwrites all existing columns by importing a CSV file, but keeps other
        columns.

        Args:
            filename: a string containing the path to the CSV file
            delimiter: a string containing the column delimiter
            decimal: a string containing the decimal separator
            thousands: a string containing the thousands separator
            header: an integer with the row number containing the column names,
                or None.
            skiprows: an integer with the number of rows to skip at start of file
        """
        self.beginResetModel()

        import_data = self._read_csv_into_dataframe(
            filename, delimiter, decimal, thousands, header, skiprows
        )
        # drop imported columns from existing data, ignore missing columns
        old_data = self._data.drop(import_data.columns, axis="columns", errors="ignore")
        # concatenate imported and old data
        new_data = pd.concat([import_data, old_data], axis="columns")
        # drop excess rows, if imported data is shorter than old data
        final_data = new_data.iloc[: len(import_data)]

        # save final data and recalculate values in calculated columns
        self._data = final_data
        self.recalculate_all_columns()

        self.endResetModel()

    def _read_csv_into_dataframe(
        self, filename, delimiter, decimal, thousands, header, skiprows
    ):
        """Read CSV data into pandas DataFrame and normalize columns."""
        df = pd.read_csv(
            filename,
            delimiter=delimiter,
            decimal=decimal,
            thousands=thousands,
            header=header,
            skiprows=skiprows,
        )
        # make sure column names are strings, even for numbered columns
        df.columns = df.columns.astype(str)
        # normalize column names to valid python variable names
        df.columns = df.columns.map(lambda s: re.sub("\W+|^(?=\d)", "_", s))
        return df
