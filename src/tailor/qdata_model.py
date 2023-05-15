"""Data model for the tailor app.

Implements a QAbstractDataModel to contain the data values as a backend for the
table view used in the app. This class in this module mostly implements the GUI side of things, but subclasses the Tailor DataModel.
"""
import numpy as np
import pandas as pd
from PySide6 import QtCore, QtGui

from tailor.data_model import DataModel

MSG_TIMEOUT = 0


class QDataModel(QtCore.QAbstractTableModel, DataModel):
    """Data model for the tailor app.

    Implements a QAbstractDataModel to contain the data values as a backend for the
    table view used in the app. This class mostly implements the GUI side of things, but subclasses the Tailor DataModel.
    """

    def __init__(self):
        """Instantiate the class."""
        super().__init__()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """Return the number of rows in the data.

        Since a table has no hierarchy, when the parent is valid (i.e. points to
        an item in the table) this method returns 0 since an item in the table
        has no rows of itself. If the parent is invalid, return the number of
        rows in the table.

        Args:
            parent: the parent item for which to count rows [invalid]
        """
        if parent.isValid():
            return 0
        else:
            return self.num_rows()

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """Return the number of columns in the data.

        Since a table has no hierarchy, when the parent is valid (i.e. points to
        an item in the table) this method returns 0 since an item in the table
        has no columns of itself. If the parent is invalid, return the number of
        columns in the table.

        Args:
            parent: the parent item for which to count columns [invalid]
        """
        if parent.isValid():
            return 0
        else:
            return self.num_columns()

    def data(
        self,
        index: QtCore.QModelIndex,
        role: QtCore.Qt.ItemDataRole = QtCore.Qt.DisplayRole,
    ) -> str | QtGui.QBrush:
        """Return (attributes of) the data.

        This method is called by the table view to request data points or its
        attributes. For each table cell multiple calls are made, one for each
        'role'. The role indicates the type of data that is requested. For
        example, the DisplayRole indicates a string is requested to display in
        the cell. Also, a BackgroundRole indicates that the background color for
        the cell is requested. You can use this to indicate different types of
        data, e.g. calculated or input data.

        If a role is requested that is not implemented an invalid QVariant
        (None) is returned.

        Args:
            index: a reference to the requested data item.
            role: an indication what type of information is
                requested.

        Returns: The requested data or None.
        """
        row = index.row()
        col = index.column()

        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            # request for the data itself
            value = self.get_value(row, col)
            if np.isnan(value) and not self.is_calculated_column(col):
                # NaN in a data column, show as empty
                return ""
            else:
                # Show float value or "nan" in a calculated column
                return f"{value:.10g}"
        elif role == QtCore.Qt.BackgroundRole:
            # request for the background fill of the cell
            if self.is_calculated_column(col):
                if self.is_calculated_column_valid(col):
                    # Yellow
                    return QtGui.QBrush(QtGui.QColor(255, 255, 200))
                else:
                    # Red
                    return QtGui.QBrush(QtGui.QColor(255, 200, 200))
        # not implemented, return an invalid QVariant (None) per the docs
        # See Qt for Python docs -> Considerations -> API Changes
        return None

    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: QtCore.Qt.ItemDataRole = QtCore.Qt.DisplayRole,
    ):
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
            The data, if available, or an invalid QVariant (None).
        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.get_column_name(section)
            else:
                # return row number (starting from 1)
                return section + 1
        # See Qt for Python docs -> Considerations -> API Changes
        return None

    def setData(
        self,
        index: QtCore.QModelIndex,
        value: float,
        role: QtCore.Qt.ItemDataRole = QtCore.Qt.EditRole,
        *,
        skip_update=False,
    ) -> bool:
        """Set (attributes of) data values.

        This method is used to set data values in the model. The role indicates
        the type of data to set. Currently, only the EditRole is supported for
        setting values through the table view's cell editing machinery.

        Args:
            index: a QModelIndex referencing the requested data item.
            value: the value to set.
            role: an ItemDataRole to indicate what type of information is
                requested.
            skip_update (boolean): if True, do not recalculate computed
                cell values or signal that the current cell has changed. These
                are both time-consuming operations.

        Returns:
            True if the data could be set. False otherwise.
        """
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            finally:
                self.set_value(row, col, value)
                # FIXME: data changed, recalculate all columns; better to only
                # recalculate the current row
                if not skip_update:
                    self.recalculate_all_columns()
                    self.dataChanged.emit(index, index)
            return True
        # Role not implemented
        return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
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

    def insertRows(
        self, row: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        """Insert rows into the table.

        Insert `count` rows into the table at position `row`. Returns True if
        the insertion was succesful.

        Args:
            row: an integer row number to indicate the place of insertion.
            count: number of rows to insert
            parent: a QModelIndex pointing into the model. Must be invalid since
                you cannot insert rows into a cell.

        Returns:
            True if the insertion was succesful, False otherwise.
        """
        if parent.isValid():
            # a table cell can _not_ insert rows
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        self.insert_rows(row, count)
        self.endInsertRows()
        self.recalculate_all_columns()
        return True

    def removeRows(
        self, row: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        """Remove rows from the table.

        Removes a row at the specified row number. Returns True if the
        removal was succesful.

        Args:
            row (int): the first row to remove
            count (int): the number of rows to remove.
            parent (QtCore.QModelIndex): a QModelIndex pointing into the model.
                Must be invalid since you cannot remove rows from a cell.

        Returns:
            True if the removal was succesful, False otherwise.
        """
        if parent.isValid():
            # a table cell can _not_ remove rows
            return False

        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        self.remove_rows(row, count)
        self.endRemoveRows()
        self.recalculate_all_columns()
        return True

    def insertColumns(
        self, column: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        """Insert columns into the table.

        Insert columns *before* the specified column number. Returns True if
        the insertion was succesful.

        Args:
            column: a column number to indicate the place of insertion.
            count: the number of columns to insert.
            parent: a QModelIndex pointing to the model. Must be invalid since
                you can't insert columns into a cell.

        Returns:
            True if the insertion was succesful, False otherwise.
        """
        if parent.isValid():
            # a table cell can _not_ insert columns
            return False

        labels = [self._create_new_column_label() for _ in range(count)]

        self.beginInsertColumns(QtCore.QModelIndex(), column, column)
        for idx, label in zip(range(column, column + count), labels):
            self._data.insert(idx, label, np.nan)
        self.endInsertColumns()
        return True

    def removeColumns(
        self, column: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        """Remove columns from the table.

        Removes a column at the specified column number. Returns True if the
        removal was succesful.

        Args:
            column: a column number to indicate the place of removal.
            count: the number of columns to remove.
            parent: a QModelIndex pointing to the model. Must be invalid since
                you can't remove columns from a cell.

        Returns:
            True if the removal was succesful, False otherwise.
        """
        if parent.isValid():
            # a table cell can _not_ remove columns
            return False

        labels = self._data.columns[column : column + count]
        self.beginRemoveColumns(QtCore.QModelIndex(), column, column)
        self._data.drop(columns=labels, inplace=True)
        # try:
        #     del self._calculated_column_expression[column_name]
        # except KeyError:
        #     # not a calculated column
        #     pass
        self.endRemoveColumns()
        # self.recalculate_all_columns()
        return True

    def moveColumn(
        self, sourceParent, sourceColumn, destinationParent, destinationChild
    ):
        """Move column.

        Move a column from sourceColumn to destinationChild. Alas, the Qt naming
        scheme remains a bit of a mystery.

        Args:
            sourceParent: ignored.
            sourceColumn (int): the source column number.
            destinationParent: ignored.
            destinationChild (int): the destination column number.

        Returns:
            bool: True if the column was moved.
        """
        cols = list(self._data.columns)
        cols.insert(destinationChild, cols.pop(sourceColumn))
        self._data = self._data[cols]
        return True

    # def show_status(self, msg):
    #     """Show message in statusbar.

    #     Args:
    #         msg (str): the error message.
    #     """
    #     self.main_window.ui.statusbar.showMessage(msg, timeout=MSG_TIMEOUT)

    # def emit_column_changed(self, col_name):
    #     """Emit dataChanged signal for a given column.

    #     Args:
    #         col_name (str): name of the column that contains updated values.
    #     """
    #     col = self._data.columns.get_loc(col_name)
    #     n_rows = len(self._data)
    #     begin = self.createIndex(0, col)
    #     end = self.createIndex(n_rows - 1, col)
    #     self.dataChanged.emit(begin, end)
