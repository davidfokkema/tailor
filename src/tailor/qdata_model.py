"""Data model for the tailor app.

Implements a QAbstractDataModel to contain the data values as a backend for the
table view used in the app. This class in this module mostly implements the GUI side of things, but subclasses the Tailor DataModel.
"""
import numpy as np
from PySide6 import QtCore, QtGui

from tailor.data_model import DataModel

MSG_TIMEOUT = 0


class QDataModel(QtCore.QAbstractTableModel):
    """Data model for the tailor app.

    Implements a QAbstractDataModel to contain the data values as a backend for the
    table view used in the app. This class mostly implements the GUI side of things, but subclasses the Tailor DataModel.
    """

    def __init__(self):
        """Instantiate the class."""
        super().__init__()
        self._data = DataModel()

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
            return self._data.num_rows()

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
            return self._data.num_columns()

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
        label = self._data.get_column_label(col)

        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            # request for the data itself
            value = self._data.get_value(row, col)
            if np.isnan(value) and not self._data.is_calculated_column(label):
                # NaN in a data column, show as empty
                return ""
            else:
                # Show float value or "nan" in a calculated column
                return f"{value:.10g}"
        elif role == QtCore.Qt.BackgroundRole:
            # request for the background fill of the cell
            if self._data.is_calculated_column(label):
                if self._data.is_column_valid(label):
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
                label = self._data.get_column_label(section)
                return self._data.get_column_name(label)
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
                self._data.set_value(row, col, value)
                # FIXME: data changed, recalculate all columns; better to only
                # recalculate the current row
                if not skip_update:
                    self._data.recalculate_all_columns()
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
        if not self._data.is_calculated_column(col):
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
        self._data.insert_rows(row, count)
        self.endInsertRows()
        self._data.recalculate_all_columns()
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

        self.beginRemoveRows(parent, row, row + count - 1)
        self._data.remove_rows(row, count)
        self.endRemoveRows()
        return True

    def insertColumns(
        self, column: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        """Insert columns into the table.

        Insert columns *before* the specified column number. Returns True if
        the insertion was succesful.

        Args:
            column (int): a column number to indicate the place of insertion.
            count (int): the number of columns to insert.
            parent (QtCore.QModelIndex): a QModelIndex pointing into the model.
                Must be invalid since you can't insert columns into a cell.

        Returns:
            True if the insertion was succesful, False otherwise.
        """
        if parent.isValid():
            # a table cell can _not_ insert columns
            return False

        self.beginInsertColumns(parent, column, column + count - 1)
        self._data.insert_columns(column, count)
        self.endInsertColumns()
        return True

    def removeColumns(
        self, column: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        """Remove columns from the table.

        Removes a column at the specified column number. Returns True if the
        removal was succesful.

        Args:
            column (int): a column number to indicate the place of removal.
            count (int): the number of columns to remove.
            parent (QtCore.QModelIndex): a QModelIndex pointing to the model.
                Must be invalid since you can't remove columns from a cell.

        Returns:
            True if the removal was succesful, False otherwise.
        """
        if parent.isValid():
            # a table cell can _not_ remove columns
            return False

        self.beginRemoveColumns(parent, column, column + count - 1)
        self._data.remove_columns(column, count)
        self.endRemoveColumns()
        return True

    def moveColumn(
        self,
        sourceParent: QtCore.QModelIndex = QtCore.QModelIndex(),
        sourceColumn: int = 0,
        destinationParent: QtCore.QModelIndex = QtCore.QModelIndex(),
        destinationChild: int = 0,
    ) -> bool:
        """Move column.

        Move a column from sourceColumn to destinationChild. Alas, the Qt naming
        scheme remains a bit of a mystery. Qt conventions are a bit weird, too.
        DestinationChild is the would-be index in the initial table, _before_
        the move operation is completed. So, if you have the initial state:

            col0, col1, col2, col3

        and you want to end up with the final state:

            col1, col2, col0, col3

        you want the operation:

            col0, col1, col2, col3
              |--------------^

        and you should call `moveColumn(0, 3)` to move col0 from index 0 to be
        inserted at index 3, i.e. you want to place col0 _before_ col3. This +1
        behaviour does not occur when moving a column to the left instead of to
        the right since then you don't have to adjust for the removal of the
        source column. So pay attention to the correct arguments.

        Args:
            sourceParent (QtCore.QModelIndex): a QModelIndex pointing to the
                model. Must be invalid since you can't move columns inside a
                cell.
            sourceColumn (int): the source column number.
            destinationParent (QtCore.QModelIndex): a QModelIndex pointing to
                the model. Must be invalid since you can't move columns inside a
                cell.
            destinationChild (int): the destination column number.

        Returns:
            bool: True if the column was moved.
        """
        if sourceParent.isValid() or destinationParent.isValid():
            # a table cell can _not_ move columns
            return False

        if self.beginMoveColumns(
            sourceParent,
            sourceColumn,
            sourceColumn,
            destinationParent,
            destinationChild,
        ):
            source_idx = sourceColumn
            dest_idx = destinationChild
            if source_idx < dest_idx:
                # Adjust for Qt conventions, undo +1, see docstring
                dest_idx -= 1
            self._data.move_column(source_idx, dest_idx)
            self.endMoveColumns()
            return True
        else:
            return False

    def insertCalculatedColumn(
        self, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        """Insert a calculated column into the table.

        Insert column *before* the specified column number. Returns True if
        the insertion was succesful.

        Args:
            column (int): a column number to indicate the place of insertion.
            parent (QtCore.QModelIndex): a QModelIndex pointing into the model.
                Must be invalid since you can't insert columns into a cell.

        Returns:
            True if the insertion was succesful, False otherwise.
        """
        if parent.isValid():
            # a table cell can _not_ insert columns
            return False

        self.beginInsertColumns(parent, column, column)
        self._data.insert_calculated_column(column)
        self.endInsertColumns()
        return True

    def columnName(self, column: int) -> str:
        """Get column name.

        Args:
            column (int): the column index.

        Returns:
            str: the column name
        """
        label = self._data.get_column_label(column)
        return self._data.get_column_name(label)

    def columnNames(self) -> list[str]:
        """Get all column names.

        Returns:
            list[str]: a list of all column names.
        """
        return self._data.get_column_names()

    def renameColumn(self, column: int, name: str) -> str:
        label = self._data.get_column_label(column)
        return self._data.rename_column(label, name)

    def isCalculatedColumn(self, column: int):
        label = self._data.get_column_label(column)
        return self._data.is_calculated_column(label)

    def columnExpression(self, column: int):
        """Get column expression.

        Get the mathematical expression for a calculated column.

        Args:
            column (int): the column index.

        Returns:
            str | None: the mathematical expression
        """
        label = self._data.get_column_label(column)
        return self._data.get_column_expression(label)

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
