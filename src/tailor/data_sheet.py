import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from tailor import dialogs
from tailor.qdata_model import MSG_TIMEOUT, QDataModel
from tailor.ui_data_sheet import Ui_DataSheet


class DataSheet(QtWidgets.QWidget):
    def __init__(self, name, main_window):
        super().__init__()
        self.ui = Ui_DataSheet()
        self.ui.setupUi(self)

        self.name = name
        self.main_window = main_window
        self.clipboard = QtWidgets.QApplication.clipboard()

        self.setup_data_model()

        self.connect_ui_events()
        self.setup_keyboard_shortcuts()

        # Start at (0, 0)
        self.ui.data_view.setCurrentIndex(self.data_model.createIndex(0, 0))

    def connect_ui_events(self):
        # connect button signals
        self.ui.add_column_button.clicked.connect(self.add_column)
        self.ui.add_calculated_column_button.clicked.connect(self.add_calculated_column)
        # user interface events
        self.ui.data_view.horizontalHeader().sectionMoved.connect(self.column_moved)
        self.ui.name_edit.textEdited.connect(self.rename_column)
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
        self.data_model = QDataModel()
        self.data_model.insertColumns(0, 2)
        self.data_model.insertRows(0, 5)

        # Set view and selection model
        self.ui.data_view.setModel(self.data_model)
        self.ui.data_view.setDragDropMode(QtWidgets.QTableView.NoDragDrop)

        # Set up header
        header = self.ui.data_view.horizontalHeader()
        header.setSectionsMovable(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setMinimumSectionSize(header.defaultSectionSize())

    def add_column(self):
        """Add column to data model and select it."""
        col_index = self.data_model.columnCount()
        self.data_model.insertColumn(col_index)
        self.ui.data_view.selectColumn(col_index)
        self.ui.name_edit.selectAll()
        self.ui.name_edit.setFocus()

    def add_calculated_column(self):
        """Add a calculated column to data model and select it."""
        col_index = self.data_model.columnCount()
        self.data_model.insertCalculatedColumn(col_index)
        self.ui.data_view.selectColumn(col_index)
        self.ui.name_edit.selectAll()
        self.ui.name_edit.setFocus()

    def add_row(self):
        """Add row to data model."""
        self.data_model.insertRow(self.data_model.rowCount())

    def remove_column(self):
        """Remove selected column(s) from data model."""
        selected_columns = [s.column() for s in self.selection.selectedColumns()]
        if selected_columns:
            # Remove columns in reverse order to avoid index shifting during
            # removal. WIP: It would be more efficient to merge ranges of
            # contiguous columns since they can be removed in one fell swoop.
            selected_columns.sort(reverse=True)
            for column in selected_columns:
                self.data_model.removeColumn(column)
        else:
            dialogs.show_warning_dialog(
                parent=self, msg="You must select one or more columns."
            )

    def remove_row(self):
        """Remove selected row(s) from data model."""
        selected_rows = [s.row() for s in self.selection.selectedRows()]
        if selected_rows:
            # Remove rows in reverse order to avoid index shifting during
            # removal. WIP: It would be more efficient to merge ranges of
            # contiguous rows since they can be removed in one fell swoop.
            selected_rows.sort(reverse=True)
            for row in selected_rows:
                self.data_model.removeRow(row)
        else:
            dialogs.show_warning_dialog(
                parent=self, msg="You must select one or more rows."
            )

    def rename_column(self, name):
        """Rename a column.

        Renames the currently selected column.

        Args:
            name: a QString containing the new name.
        """
        if self._selected_col_idx is not None:
            # Do not allow empty names or duplicate column names
            if name and name not in self.data_model.get_column_names():
                old_name = self.data_model.get_column_name(self._selected_col_idx)
                new_name = self.data_model.rename_column(self._selected_col_idx, name)
                self.main_window.rename_plot_variables(self, old_name, new_name)
                # set the normalized name to the name edit field
                self.ui.name_edit.setText(new_name)

    def update_column_expression(self, expression):
        """Update a column expression.

        Tries to recalculate the values of the currently selected column in the
        data model.

        Args:
            expression: a QString containing the mathematical expression.
        """
        if self._selected_col_idx is not None:
            self.data_model.update_column_expression(self._selected_col_idx, expression)

    def selection_changed(self, selected, deselected):
        """Handle selectionChanged events in the data view.

        When the selection is changed, the column index of the left-most cell in
        the first selection is used to identify the column name and the
        mathematical expression that is used to calculate the column values.
        These values are used to update the column information in the user
        interface.

        Args:
            selected: QItemSelection containing the newly selected events.
            deselected: QItemSelection containing previously selected, and now
            deselected, items.
        """
        if not selected.isEmpty():
            self.ui.nameLabel.setEnabled(True)
            self.ui.name_edit.setEnabled(True)
            first_selection = selected.first()
            col_idx = first_selection.left()
            self._selected_col_idx = col_idx
            self.ui.name_edit.setText(self.data_model.columnName(col_idx))
            self.ui.formula_edit.setText(self.data_model.columnExpression(col_idx))
            if self.data_model.isCalculatedColumn(col_idx):
                self.ui.formulaLabel.setEnabled(True)
                self.ui.formula_edit.setEnabled(True)
            else:
                self.ui.formulaLabel.setEnabled(False)
                self.ui.formula_edit.setEnabled(False)
        else:
            self.ui.nameLabel.setEnabled(False)
            self.ui.name_edit.clear()
            self.ui.name_edit.setEnabled(False)
            self.ui.formulaLabel.setEnabled(False)
            self.ui.formula_edit.clear()
            self.ui.formula_edit.setEnabled(False)

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

        Args:
            logidx (int): the logical column index (index in the dataframe)
            oldidx (int): the old visual index newidx (int): the new visual
            index
        """
        print(f"Column moved from {oldidx=} to {newidx=}")
        header = self.ui.data_view.horizontalHeader()
        header.blockSignals(True)
        # move the column back, keep the header in logical order
        header.moveSection(newidx, oldidx)
        header.blockSignals(False)
        # move the underlying data column instead
        self.data_model.moveColumn(None, oldidx, None, newidx)
        self.data_model.recalculate_all_columns()
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
        for index in self.selection.selectedIndexes():
            self.data_model.setData(index, "", skip_update=True)
        # signal that ALL values may have changed using an invalid index
        # this can be MUCH quicker than emitting signals for each cell
        self.data_model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        # recalculate computed values once
        self.data_model.recalculate_all_columns()

    def get_index_below_selected_cell(self):
        """Get index directly below the selected cell."""
        return self.ui.data_view.moveCursor(
            QtWidgets.QTableView.MoveDown, QtCore.Qt.NoModifier
        )

    def copy_selected_cells(self):
        """Copy selected cells to clipboard."""

        # get bounding rectangle coordinates and sizes
        selection = self.selection.selection().toList()
        left = min(r.left() for r in selection)
        width = max(r.right() for r in selection) - left + 1
        top = min(r.top() for r in selection)
        height = max(r.bottom() for r in selection) - top + 1

        # fill data from selected indexes, not selected -> NaN
        data = np.full((height, width), np.nan)
        for index in self.selection.selectedIndexes():
            if (value := index.data()) == "":
                value = np.nan
            data[index.row() - top, index.column() - left] = value

        # create tab separated values from data, NaN -> empty string, e.g.
        # 1 2 3
        # 2   4
        # 5 5 6
        text = "\n".join(
            [
                "\t".join([str(v) if not np.isnan(v) else "" for v in row])
                for row in data
            ]
        )

        # write TSV text to clipboard
        self.clipboard.setText(text)

    def paste_cells(self):
        """Paste cells from clipboard."""

        # get data from clipboard
        text = self.clipboard.text()

        # create array from tab separated values, "" -> NaN
        try:
            data = np.array(
                [
                    [float(v) if v != "" else np.nan for v in row.split("\t")]
                    for row in text.split("\n")
                ]
            )
        except ValueError as exc:
            self.main_window.ui.statusbar.showMessage(
                f"Error pasting from clipboard: {exc}", timeout=MSG_TIMEOUT
            )
            return

        # get current coordinates and data size
        current_index = self.ui.data_view.currentIndex()
        start_row, start_column = current_index.row(), current_index.column()
        height, width = data.shape

        # extend rows and columns if necessary
        last_table_column = self.data_model.columnCount() - 1
        if (last_data_column := start_column + width - 1) > last_table_column:
            for _ in range(last_data_column - last_table_column):
                self.add_column()
        last_table_row = self.data_model.rowCount() - 1
        if (last_data_row := start_row + height - 1) > last_table_row:
            for _ in range(last_data_row - last_table_row):
                self.add_row()

        # write clipboard data to data model
        it = np.nditer(data, flags=["multi_index"])
        for value in it:
            row, column = it.multi_index
            self.data_model.setData(
                self.data_model.createIndex(row + start_row, column + start_column),
                value,
                skip_update=True,
            )

        # signal that values have changed
        top_left = self.data_model.createIndex(start_row, start_column)
        bottom_right = self.data_model.createIndex(
            start_row + height - 1, start_column + width - 1
        )
        self.data_model.dataChanged.emit(top_left, bottom_right)
        # recalculate computed values once
        self.data_model.recalculate_all_columns()
        # reset current index and focus
        self.ui.data_view.setFocus()
        # set selection to pasted cells
        selection = QtCore.QItemSelection(top_left, bottom_right)
        self.selection.select(selection, self.selection.ClearAndSelect)
