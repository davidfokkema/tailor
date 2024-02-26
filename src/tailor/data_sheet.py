import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from tailor import dialogs
from tailor.qdata_model import MSG_TIMEOUT, QDataModel
from tailor.ui_data_sheet import Ui_DataSheet


class DataSheet(QtWidgets.QWidget):
    model: QDataModel = None
    selection: QtCore.QItemSelectionModel
    name: str = None
    id: int

    def __init__(self, name, id, main_window):
        super().__init__()
        self.ui = Ui_DataSheet()
        self.ui.setupUi(self)

        self.name = name
        self.id = id
        self.main_window = main_window
        self.clipboard = QtWidgets.QApplication.clipboard()

        self.setup_data_model()

        self.connect_ui_events()
        self.setup_keyboard_shortcuts()

        # Start at (0, 0)
        self.ui.data_view.setCurrentIndex(self.model.createIndex(0, 0))

    def connect_ui_events(self):
        # connect button signals
        self.ui.add_column_button.clicked.connect(self.add_column)
        self.ui.add_calculated_column_button.clicked.connect(self.add_calculated_column)
        # user interface events
        self.ui.data_view.horizontalHeader().sectionMoved.connect(self.column_moved)
        self.ui.name_edit.textEdited.connect(self.rename_selected_column)
        self.ui.formula_edit.textEdited.connect(self.update_column_expression)
        self.ui.create_plot_button.clicked.connect(
            self.main_window.ask_and_create_plot_tab
        )
        # Set up selection events
        self.selection = self.ui.data_view.selectionModel()
        self.selection.selectionChanged.connect(self.selection_changed)

    def setup_keyboard_shortcuts(self):
        # Create shortcut for return/enter keys
        for key in QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter:
            QtGui.QShortcut(
                QtGui.QKeySequence(key), self.ui.data_view, self.edit_or_move_down
            )
        # Shortcut for backspace and delete: clear cell contents
        for key in QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete:
            QtGui.QShortcut(
                QtGui.QKeySequence(key), self.ui.data_view, self.clear_selected_cells
            )

    def setup_data_model(self):
        """Set up the data model with some initial data."""
        self.model = QDataModel(main_window=self.main_window)
        self.model.insertColumns(0, 2)
        self.model.insertRows(0, 5)

        # Set view and selection model
        self.ui.data_view.setModel(self.model)
        self.ui.data_view.setDragDropMode(QtWidgets.QTableView.NoDragDrop)

        # Set up header
        header = self.ui.data_view.horizontalHeader()
        header.setSectionsMovable(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setMinimumSectionSize(header.defaultSectionSize())

    def add_column(self):
        """Add column to data model and select it."""
        col_index = self.model.columnCount()
        self.model.insertColumn(col_index)
        self.ui.data_view.selectColumn(col_index)
        self.ui.name_edit.selectAll()
        self.ui.name_edit.setFocus()

    def add_calculated_column(self):
        """Add a calculated column to data model and select it."""
        col_index = self.model.columnCount()
        self.model.insertCalculatedColumn(col_index)
        self.ui.data_view.selectColumn(col_index)
        self.ui.name_edit.selectAll()
        self.ui.name_edit.setFocus()

    def add_row(self):
        """Add row to data model."""
        self.model.insertRow(self.model.rowCount())

    def get_selected_column_labels(self) -> list[str]:
        """Get labels for currently selected columns.

        Returns:
            list[str]: the column labels.
        """
        selected_columns = [s.column() for s in self.selection.selectedColumns()]
        return [self.model.columnLabel(idx) for idx in selected_columns]

    def remove_selected_columns(self):
        """Remove selected column(s) from data model."""
        selected_columns = [s.column() for s in self.selection.selectedColumns()]
        if selected_columns:
            # Remove columns in reverse order to avoid index shifting during
            # removal. WIP: It would be more efficient to merge ranges of
            # contiguous columns since they can be removed in one fell swoop.
            selected_columns.sort(reverse=True)
            for column in selected_columns:
                self.model.removeColumn(column)
        else:
            dialogs.show_warning_dialog(
                parent=self, msg="You must select one or more columns."
            )

    def remove_selected_row(self):
        """Remove selected row(s) from data model."""
        selected_rows = [s.row() for s in self.selection.selectedRows()]
        if selected_rows:
            # Remove rows in reverse order to avoid index shifting during
            # removal. WIP: It would be more efficient to merge ranges of
            # contiguous rows since they can be removed in one fell swoop.
            selected_rows.sort(reverse=True)
            for row in selected_rows:
                self.model.removeRow(row)
        else:
            dialogs.show_warning_dialog(
                parent=self, msg="You must select one or more rows."
            )

    def rename_selected_column(self, name):
        """Rename a column.

        Renames the currently selected column.

        Args:
            name: a QString containing the new name.
        """
        col_idx = self._selected_col_idx
        if col_idx is not None:
            # Do not allow empty names or duplicate column names
            if name and name not in self.model.columnNames():
                new_name = self.model.renameColumn(col_idx, name)
                # Set the normalized name to the name edit field. This can
                # change the cursor position because characters may be replaced
                # (like spaces or digits at the start of the string). Move the
                # cursor to the 'expected' position: static with respect to the
                # end of the string.
                pos_from_end = len(name) - self.ui.name_edit.cursorPosition()
                new_pos = len(new_name) - pos_from_end
                self.ui.name_edit.setText(new_name)
                self.ui.name_edit.setCursorPosition(new_pos)
                header = self.ui.data_view.horizontalHeader()
                header.headerDataChanged(QtCore.Qt.Horizontal, col_idx, col_idx)

    def update_column_expression(self, expression):
        """Update a column expression.

        Tries to recalculate the values of the currently selected column in the
        data model.

        Args:
            expression: a QString containing the mathematical expression.
        """
        if self._selected_col_idx is not None:
            self.model.updateColumnExpression(self._selected_col_idx, expression)
            self.update_expression_border(self._selected_col_idx)

    def selection_changed(self, selected=None, deselected=None):
        """Handle selectionChanged events in the data view.

        When the selection is changed, the column index of the left-most cell in
        the first selection is used to identify the column name and the
        mathematical expression that is used to calculate the column values.
        These values are used to update the column information in the user
        interface.

        Note: the selected and deselected parameters are ignored. They only tell
        you about the changes in selection being made. So, for example, if you
        first select a column and then select a single cell within that column,
        selected will be empty (no extra cells selected) and deselected will
        contain all other cells in the column. This is not very useful to
        determine the current selection. Therefore, the current selection is
        retrieved instead of using the arguments.

        Args:
            selected: QItemSelection containing the newly selected cells.
            deselected: QItemSelection containing previously selected, and now
            deselected, items.
        """
        selected = self.selection.selection()
        if not selected.isEmpty():
            self.ui.nameLabel.setEnabled(True)
            self.ui.name_edit.setEnabled(True)
            first_selection = selected.first()
            col_idx = first_selection.left()
            self._selected_col_idx = col_idx
            self.ui.name_edit.setText(self.model.columnName(col_idx))
            self.ui.formula_edit.setText(self.model.columnExpression(col_idx))
            if self.model.isCalculatedColumn(col_idx):
                self.ui.formulaLabel.setEnabled(True)
                self.ui.formula_edit.setEnabled(True)
            else:
                self.ui.formulaLabel.setEnabled(False)
                self.ui.formula_edit.setEnabled(False)
            self.update_expression_border(col_idx)
        else:
            self.ui.nameLabel.setEnabled(False)
            self.ui.name_edit.clear()
            self.ui.name_edit.setEnabled(False)
            self.ui.formulaLabel.setEnabled(False)
            self.ui.formula_edit.clear()
            self.ui.formula_edit.setEnabled(False)

    def update_expression_border(self, col_idx: int) -> None:
        """Update border of the calculated column expression widget.

        If the expression is not valid, draw a red border around the widget.

        Args:
            col_idx (int): the column index.
        """
        if self.model.data_model.is_column_valid(self.model.columnLabel(col_idx)):
            self.ui.formula_edit.setStyleSheet("border: 0px")
        else:
            self.ui.formula_edit.setStyleSheet("border: 1px solid red")

    def column_moved(self, logidx, oldidx, newidx):
        """Move column in reaction to UI signal.

        Dragging a column to a new location triggers execution of this method.
        Since the UI only reorders the column visually and does not change the
        underlying data, things can get tricky when trying to determine which
        variables are available to the left of calculated columns and which
        columns include the bouding box of a selection for copy/paste. So, we
        will immediately move back the column in the view and move the
        underlying data instead. That way, visual and logical ordering are
        always in sync.

        Qt conventions are a bit weird and inconsistent, unfortunately. Moving a
        column requires calling the moveColumn() method with sourceIndex and
        destinationChild parameters. DestinationChild is the would-be index in
        the initial table, _before_ the move operation is completed. So, if you
        have the initial state:

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
        source column.

        The problem is that newidx does _not_ behave that way. The argument
        oldidx works on the initial state and the argument newidx works on the
        final state. So the above move operation `moveColumn(0, 3)` has
        oldidx = 0 and newidx = 2 (check the final state).

        Args:
            logidx (int): the logical column index (index in the dataframe)
            oldidx (int): the old visual index newidx (int): the new visual
            index
        """
        # Raise an exception when column ordering has been messed up
        assert logidx == oldidx

        header = self.ui.data_view.horizontalHeader()
        header.blockSignals(True)
        # move the column back, keep the header in logical order
        header.moveSection(newidx, oldidx)
        header.blockSignals(False)
        # move the underlying data column instead
        if newidx > oldidx:
            # moving to the right
            destidx = newidx + 1
        else:
            destidx = newidx
        self.model.moveColumn(sourceColumn=oldidx, destinationChild=destidx)
        # select the column that was just moved at the new location
        self.ui.data_view.selectColumn(newidx)

    def edit_or_move_down(self):
        """Edit cell or move cursor down a row.

        Start editing a cell. If the cell was already being edited, move the
        cursor down a row, stopping the edit in the process. Trigger a
        recalculation of all calculated columns.
        """
        cur_index = self.ui.data_view.currentIndex()
        if not self.ui.data_view.isPersistentEditorOpen(cur_index):
            # is not yet editing, so start an edit
            self.ui.data_view.edit(cur_index)
        else:
            # is already editing, what index is below?
            new_index = self.get_index_below_selected_cell()
            if new_index == cur_index:
                # already on bottom row, create a new row and take that index
                self.add_row()
                new_index = self.get_index_below_selected_cell()
            # move to it (finishing editing in the process)
            self.ui.data_view.setCurrentIndex(new_index)

    def clear_selected_cells(self):
        """Clear contents of selected cells."""
        self.model.clearData(self.selection.selection())

    def get_index_below_selected_cell(self):
        """Get index directly below the selected cell."""
        return self.ui.data_view.moveCursor(
            QtWidgets.QTableView.MoveDown, QtCore.Qt.NoModifier
        )

    def copy_selected_cells(self):
        """Copy selected cells to clipboard."""

        data = self.model.dataFromSelection(self.selection.selection())
        text = self.array_to_text(data)
        self.clipboard.setText(text)

    def paste_cells(self):
        """Paste cells from clipboard."""

        text = self.clipboard.text()
        values = self.text_to_array(text)
        if isinstance(values, np.ndarray):
            current_index = self.ui.data_view.currentIndex()
            self.model.setDataFromArray(current_index, values)

        # FIXME
        # # reset current index and focus
        # self.ui.data_view.setFocus()
        # # set selection to pasted cells
        # selection = QtCore.QItemSelection(top_left, bottom_right)
        # self.selection.select(selection, self.selection.ClearAndSelect)

    def array_to_text(self, data: np.ndarray) -> str:
        # create tab separated values from data, NaN -> empty string, e.g.
        # 1 2 3
        # 2   4
        # 5 5 6
        return "\n".join(
            [
                "\t".join([str(v) if not np.isnan(v) else "" for v in row])
                for row in data
            ]
        )

    def text_to_array(self, text: str) -> np.ndarray | None:
        """Convert tab-separated values to an array.

        Args:
            text (str): a multi-line string of tab-separated values.

        Returns:
            np.ndarray: the data as a NumPy array
        """
        if not text:
            return None
        try:
            # create array from tab separated values, "" -> NaN
            values = np.array(
                [
                    [float(v) if v != "" else np.nan for v in row.split("\t")]
                    for row in text.split("\n")
                ]
            )
        except ValueError as exc:
            self.main_window.ui.statusbar.showMessage(
                f"Error pasting from clipboard: {exc}", timeout=MSG_TIMEOUT
            )
            return None
        else:
            return values
