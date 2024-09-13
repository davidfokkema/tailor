"""Data model for the tailor app.

Implements a QAbstractDataModel to contain the data values as a backend for the
table view used in the app. This class in this module mostly implements the GUI side of things, but subclasses the Tailor DataModel.
"""

import pathlib

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from tailor.csv_format_dialog import FormatParameters
from tailor.data_model import DataModel

MSG_TIMEOUT = 0


class QDataModel(QtCore.QAbstractTableModel):
    """Qt Data model for the data sheets.

    Implements a QAbstractDataModel to contain the data values as a backend for
    the table view used in the app. This class mostly implements the GUI side of
    things. The underlying data is handled by DataModel.
    """

    def __init__(self, main_window):
        """Instantiate the class."""
        super().__init__()
        self.data_model = DataModel()
        self.main_window = main_window

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
            return self.data_model.num_rows()

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
            return self.data_model.num_columns()

    def data(
        self,
        index: QtCore.QModelIndex,
        role: QtCore.Qt.ItemDataRole = QtCore.Qt.DisplayRole,
    ) -> str | QtGui.QBrush | None:
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
        label = self.data_model.get_column_label(col)

        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize()
        elif role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            # request for the data itself
            value = self.data_model.get_value(row, col)
            if np.isnan(value) and not self.data_model.is_calculated_column(label):
                # NaN in a data column, show as empty
                return ""
            else:
                if role == QtCore.Qt.EditRole:
                    # when editing, the default delegate for floats is too restrictive
                    # return a string, so we get a free-form string edit widget
                    return str(value)
                else:
                    # Show float value or "nan" in a calculated column
                    return float(value)
        elif role == QtCore.Qt.BackgroundRole:
            # request for the background fill of the cell
            if self.data_model.is_calculated_column(label):
                if self.data_model.is_column_valid(label):
                    if self.dark_mode_enabled():
                        return QtGui.QBrush(QtGui.QColor(75, 75, 0))
                    else:
                        # Yellow
                        return QtGui.QBrush(QtGui.QColor(255, 255, 200))
                else:
                    if self.dark_mode_enabled():
                        return QtGui.QBrush(QtGui.QColor(100, 00, 00))
                    else:
                        # Red
                        return QtGui.QBrush(QtGui.QColor(255, 200, 200))
        # not implemented, return an invalid QVariant (None) per the docs
        # See Qt for Python docs -> Considerations -> API Changes
        return None

    def dark_mode_enabled(self) -> bool:
        """Check if dark mode is enabled."""
        return (
            QtWidgets.QApplication.instance().styleHints().colorScheme()
            == QtCore.Qt.ColorScheme.Dark
        )

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
                label = self.data_model.get_column_label(section)
                return self.data_model.get_column_name(label)
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
                self.data_model.set_value(row, col, value)
            self.main_window.mark_project_dirty()
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
        label = self.data_model.get_column_label(index.column())
        if not self.data_model.is_calculated_column(label):
            # You can only edit data if the column values are not calculated
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def insertRows(
        self, row: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        """Insert rows into the table.

        Insert `count` rows into the table at position `row`. Returns True if
        the insertion was succesful and False otherwise. Note that you cannot
        insert rows into a table which has no columns. So, first ensure the
        table contains some columns before inserting rows.

        Args:
            row: an integer row number to indicate the place of insertion.
            count: number of rows to insert parent: a QModelIndex pointing into
            the model. Must be invalid since
                you cannot insert rows into a cell.

        Returns:
            True if the insertion was succesful, False otherwise.
        """
        if parent.isValid():
            # a table cell can _not_ insert rows
            return False

        if self.data_model.num_columns() == 0:
            # you can not insert rows when there are no columns
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        self.data_model.insert_rows(row, count)
        self.endInsertRows()
        self.main_window.mark_project_dirty()
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
        self.data_model.remove_rows(row, count)
        self.endRemoveRows()
        self.main_window.mark_project_dirty()
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
        self.data_model.insert_columns(column, count)
        self.endInsertColumns()
        self.main_window.mark_project_dirty()
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
        self.data_model.remove_columns(column, count)
        self.endRemoveColumns()
        self.main_window.mark_project_dirty()
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
            self.data_model.move_column(source_idx, dest_idx)
            # endMoveColumns triggers a dataChanged for all columns, apparently
            self.endMoveColumns()
            self.main_window.mark_project_dirty()
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
        self.data_model.insert_calculated_column(column)
        self.endInsertColumns()
        self.main_window.mark_project_dirty()
        return True

    def columnLabel(self, column: int) -> str:
        """Get column label.

        Args:
            column (int): the column index.

        Returns:
            str: the column label
        """
        return self.data_model.get_column_label(column)

    def columnName(self, column: int) -> str:
        """Get column name.

        Args:
            column (int): the column index.

        Returns:
            str: the column name
        """
        label = self.data_model.get_column_label(column)
        return self.data_model.get_column_name(label)

    def columnLabels(self) -> list[str]:
        """Get all column labels.

        Returns:
            list[str]: a list of all column labels.
        """
        return self.data_model.get_column_labels()

    def columnNames(self) -> list[str]:
        """Get all column names.

        Returns:
            list[str]: a list of all column names.
        """
        return self.data_model.get_column_names()

    def renameColumn(self, column: int, name: str) -> str:
        label = self.data_model.get_column_label(column)
        self.main_window.mark_project_dirty()
        return self.data_model.rename_column(label, name)

    def isCalculatedColumn(self, column: int):
        label = self.data_model.get_column_label(column)
        return self.data_model.is_calculated_column(label)

    def columnExpression(self, column: int):
        """Get column expression.

        Get the mathematical expression for a calculated column.

        Args:
            column (int): the column index.

        Returns:
            str | None: the mathematical expression
        """
        label = self.data_model.get_column_label(column)
        return self.data_model.get_column_expression(label)

    def columnUses(self, column: int, column_labels: list[str]) -> bool:
        """Test whether column uses any of the listed columns.

        If the column is a calculated column and uses any of the supplied
        `column_labels` in its expression, return True.

        Args:
            column (int): the column under test.
            column_labels (list[str]): a list of column labels.

        Returns:
            bool: True if the column uses any of the column_labels.
        """
        label = self.data_model.get_column_label(column)
        return self.data_model.column_uses(label, column_labels)

    def updateColumnExpression(self, column: int, expression: str) -> bool:
        if not self.isCalculatedColumn(column):
            return False
        label = self.data_model.get_column_label(column)
        self.data_model.update_column_expression(label, expression)
        top_left = self.createIndex(0, column)
        bottom_right = self.createIndex(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)
        self.main_window.mark_project_dirty()
        return True

    def clearData(self, selection: QtCore.QItemSelection) -> bool:
        """Clear all cell contents within a selection.

        Args:
            selection (QtCore.QItemSelection): selection of cells to clear

        Returns:
            bool: True if successful.
        """
        for selection_range in selection.toList():
            self.data_model.set_values(
                selection_range.top(),
                selection_range.left(),
                selection_range.bottom(),
                selection_range.right(),
                np.nan,
            )
            # recalculating vales may have changed all columns to the far right
            num_columns = self.columnCount()
            self.dataChanged.emit(
                selection_range.topLeft(),
                self.createIndex(selection_range.bottom(), num_columns - 1),
            )
        self.main_window.mark_project_dirty()
        return True

    def dataFromSelection(self, selection: QtCore.QItemSelection) -> np.ndarray:
        """Get data in a selection.

        Return all data values in a selection. The selection can consist of
        multiple selection ranges but the returned data is always a rectangular
        array. Positions inside the bounding rectangle which have not been
        selected will yield a NaN value.

        For example, given the data and selection:

             1  2  3  4  5  6
                 ┌─────┐
             7  8│ 9 10│11 12
                 │     │
            13 14│15 16│17 18
                 │     ├──┐
            19 20│21 22│23│24
                 └─────┴──┘
            25 26 27 28 29 30

        The result should be:

             9 10 NaN

            15 16 NaN

            21 22 223

        Args:
            selection (QtCore.QItemSelection): the selected data.

        Returns:
            np.ndarray: the data values in the selection.
        """
        # get bounding rectangle coordinates and sizes
        ranges = selection.toList()
        column_offset = min(r.left() for r in ranges)
        width = max(r.right() for r in ranges) - column_offset + 1
        row_offset = min(r.top() for r in ranges)
        height = max(r.bottom() for r in ranges) - row_offset + 1

        # fill data from selected indexes, not selected -> NaN
        data = np.full((height, width), np.nan)

        # copy values from each rectangular selection range
        for selection_range in ranges:
            top = selection_range.top()
            left = selection_range.left()
            bottom = selection_range.bottom()
            right = selection_range.right()
            values = self.data_model.get_values(top, left, bottom, right)
            data[
                top - row_offset : bottom - row_offset + 1,
                left - column_offset : right - column_offset + 1,
            ] = values
        return data

    def setDataFromArray(self, index: QtCore.QModelIndex, values: np.ndarray):
        """Fill a block of table cells with the contents of an array.

        Args:
            index (QtCore.QModelIndex): the top left corner of the block of
                cells.
            values (np.ndarray): the array containing the values.

        Returns:
            bool: True if successful.
        """
        row = index.row()
        column = index.column()
        height, width = values.shape
        if (delta_columns := column + width - self.columnCount()) > 0:
            self.insertColumns(self.columnCount(), delta_columns)
        if (delta_rows := row + height - self.rowCount()) > 0:
            self.insertRows(self.rowCount(), delta_rows)
        self.data_model.set_values_from_array(row, column, values)

        # recalculating vales may have changed all columns to the far right
        num_columns = self.columnCount()
        self.dataChanged.emit(
            index, self.createIndex(row + height - 1, num_columns - 1)
        )
        self.main_window.mark_project_dirty()
        return True

    def is_empty(self):
        """Check whether all cells are empty."""
        return self.data_model.is_empty()

    def export_csv(self, path: pathlib.Path) -> None:
        """Export all data to CSV file.

        Args:
            filename (pathlib.Path): the destination path.
        """
        self.data_model.export_csv(path)

    def import_csv(
        self,
        filename: pathlib.Path | str,
        format: FormatParameters,
    ):
        """Read data from CSV file.

        Overwrites all existing data by importing a CSV file.

        Args:
            filename (pathlib.Path | str): a string containing the path to the CSV file
            format (FormatParameters): CSV format parameters
        """
        self.beginResetModel()
        self.data_model.import_csv(filename, format)
        self.endResetModel()
        self.main_window.mark_project_dirty()

    def merge_csv(
        self,
        filename: pathlib.Path | str,
        format: FormatParameters,
    ):
        """Merge data from CSV file into existing data sheet.

        Merges imported CSV data with pre-existing data already present in the
        data sheet.

        Args:
            filename (pathlib.Path | str): a string containing the path to the CSV file
            format (FormatParameters): CSV format parameters
        """
        self.beginResetModel()
        self.data_model.merge_csv(filename, format)
        self.endResetModel()
        self.main_window.mark_project_dirty()
