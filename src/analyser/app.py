"""Analyser app.

Import datasets or enter data by hand and create plots to explore correlations.
You can fit custom models to your data to estimate best-fit parameters.
"""

import os

import sys

from PyQt5 import uic, QtWidgets, QtCore
import pyqtgraph as pg
import pkg_resources

from analyser.data_model import DataModel
from analyser.plot_tab import PlotTab

# Fix for Big Sur bug in Qt >=5.15, <15.15.2
# os.environ["QT_MAC_WANTS_LAYER"] = "1"

pg.setConfigOptions(antialias=True)
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class UserInterface(QtWidgets.QMainWindow):
    """Main user interface for the analyser app.

    The user interface centers on the table containing the data values. A single
    DataModel is instantiated to hold the data.

    """

    _selected_col_idx = None
    plot_tabs = None
    plot_num = 1

    def __init__(self):
        """Initialize the class."""

        # roep de __init__() aan van de parent class
        super().__init__()

        self.plot_tabs = []

        uic.loadUi(
            pkg_resources.resource_stream("analyser.resources", "analyser.ui"), self
        )

        self.data_model = DataModel()
        self.data_view.setModel(self.data_model)
        self.data_view.setDragDropMode(self.data_view.InternalMove)

        self.selection = self.data_view.selectionModel()
        self.selection.selectionChanged.connect(self.selection_changed)

        self.add_column_button.clicked.connect(self.add_column)

        # connect menu items
        self.actionAdd_column.triggered.connect(self.add_column)
        self.actionAdd_calculated_column.triggered.connect(self.add_calculated_column)
        self.actionAdd_row.triggered.connect(self.add_row)
        self.actionRemove_column.triggered.connect(self.remove_column)

        self.name_edit.textEdited.connect(self.rename_column)
        self.formula_edit.textEdited.connect(self.recalculate_column)
        self.create_plot_button.clicked.connect(self.ask_and_create_plot_tab)

        # Create shortcut for return/enter keys
        for key in QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter:
            QtWidgets.QShortcut(key, self.data_view, self.edit_or_move_down)

        # tests
        self.create_plot_tab("U", "I", "dU", "dI")
        self.plot_tabs[0].model_func.setText("a * U + b")
        self.plot_tabs[0].model_func.textEdited.emit("")
        # self.tabWidget.setCurrentIndex(1)
        self.plot_tabs[0].fit_button.clicked.emit()

        # test: create column, select, fill in 'a' and recalculate
        self.add_column_button.clicked.emit()
        self.data_view.setCurrentIndex(self.data_model.createIndex(0, 4))
        self.formula_edit.setText("a")
        self.formula_edit.textEdited.emit("")

        # test: remove column
        self.remove_column()

    def edit_or_move_down(self):
        """Edit cell or move cursor down a row.
        
        Start editing a cell. If the cell was already being edited, move the cursor down a row, stopping the edit in the process.
        """
        cur_index = self.data_view.currentIndex()
        if not self.data_view.isPersistentEditorOpen(cur_index):
            # is not yet editing, so start an edit
            self.data_view.edit(cur_index)
        else:
            # is already editing, what index is below?
            new_index = self.data_view.moveCursor(
                self.data_view.MoveDown, QtCore.Qt.NoModifier
            )
            if new_index != cur_index:
                # a new one, so move to it (finishing editing in the process)
                self.data_view.setCurrentIndex(new_index)
            else:
                # already on bottom row, have to manually save and close the editor
                widget = self.data_view.indexWidget(cur_index)
                self.data_view.commitData(widget)
                self.data_view.closeEditor(
                    widget, QtWidgets.QAbstractItemDelegate.NoHint
                )

    def selection_changed(self, selected, deselected):
        """Handles selectionChanged events in the data view.

        When the selection is changed, the column index of the left-most cell in
        the first selection is used to identify the column name and the
        mathematical expression that is used to calculate the column values.
        These values are used to update the column information in the user
        interface.

        Args: selected: QItemSelection containing the newly selected events.
            deselected: QItemSelection containing previously selected, and now
            deselected, items.
        """
        if not selected.isEmpty():
            first_selection = selected.first()
            col_idx = first_selection.left()
            self._selected_col_idx = col_idx
            self.name_edit.setText(self.data_model.get_column_name(col_idx))
            self.formula_edit.setText(self.data_model.get_column_expression(col_idx))

    def add_column(self):
        """Add column to data model."""
        self.data_model.insertColumn(self.data_model.columnCount())

    def add_calculated_column(self):
        """Add a calculated column to data model."""
        self.data_model.insert_calculated_column(self.data_model.columnCount())

    def add_row(self):
        """Add row to data model."""
        self.data_model.insertRow(self.data_model.rowCount())

    def remove_column(self):
        """Remove selected column(s) from data model."""
        selected_columns = [s.column() for s in self.selection.selectedColumns()]
        if selected_columns:
            for column in selected_columns:
                self.data_model.removeColumn(column)
        else:
            error_msg = QtWidgets.QMessageBox()
            error_msg.setText("You must select one or more columns.")
            error_msg.exec()

    def rename_column(self, name):
        """Rename a column.

        Renames the currently selected column.

        Args:
            name: a QString containing the new name.
        """
        if self._selected_col_idx is not None:
            if name and name not in self.data_model.get_column_names():
                # Do not allow empty names or duplicate column names
                self.data_model.rename_column(self._selected_col_idx, name)

    def recalculate_column(self):
        """Recalculate column values.

        Tries to recalculate the values of the currently selected column in the
        data model.
        """
        if self._selected_col_idx is not None:
            self.data_model.recalculate_column(
                self._selected_col_idx, self.formula_edit.text()
            )

    def ask_and_create_plot_tab(self):
        """Opens a dialog and create a new tab with a plot.

        First, a create plot dialog is opened to query the user for the columns
        to plot. When the dialog is accepted, creates a new tab containing the
        requested plot.
        """
        dialog = self.create_plot_dialog()
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            x_var = dialog.x_axis_box.currentText()
            y_var = dialog.y_axis_box.currentText()
            x_err = dialog.x_err_box.currentText()
            y_err = dialog.y_err_box.currentText()
            if x_var and y_var:
                self.create_plot_tab(x_var, y_var, x_err, y_err)

    def create_plot_tab(self, x_var, y_var, x_err, y_err):
        """Create a new tab with a plot.

        Args:
            x_var: the name of the variable to plot on the x-axis.
            y_var: the name of the variable to plot on the y-axis.
            x_err: the name of the variable to use for the x-error bars.
            y_err: the name of the variable to use for the y-error bars.
        """
        plot_tab = PlotTab(self.data_model)
        self.plot_tabs.append(plot_tab)
        self.tabWidget.addTab(plot_tab, f"Plot {self.plot_num}")
        self.plot_num += 1
        plot_tab.create_plot(x_var, y_var, x_err, y_err)

    def create_plot_dialog(self):
        """Create a dialog to request variables for creating a plot."""
        create_dialog = QtWidgets.QDialog(parent=self)
        uic.loadUi(
            pkg_resources.resource_stream(
                "analyser.resources", "create_plot_dialog.ui"
            ),
            create_dialog,
        )
        choices = [None] + self.data_model.get_column_names()
        create_dialog.x_axis_box.addItems(choices)
        create_dialog.y_axis_box.addItems(choices)
        create_dialog.x_err_box.addItems(choices)
        create_dialog.y_err_box.addItems(choices)
        return create_dialog


def main():
    """Main entry point."""
    app = QtWidgets.QApplication(sys.argv)
    ui = UserInterface()
    ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
