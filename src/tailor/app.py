"""Tailor app.

Import datasets or enter data by hand and create plots to explore correlations.
You can fit custom models to your data to estimate best-fit parameters.
"""

import gzip
from importlib import metadata as importlib_metadata
import json
import os
import pathlib
import sys

from PyQt5 import uic, QtWidgets, QtCore
import pyqtgraph as pg
import pkg_resources

from tailor.data_model import DataModel
from tailor.plot_tab import PlotTab


app_module = sys.modules["__main__"].__package__
metadata = importlib_metadata.metadata(app_module)
__name__ = metadata["name"]
__version__ = metadata["version"]


# FIXME: antialiasing is EXTREMELY slow. Why?
# pg.setConfigOptions(antialias=True)
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class UserInterface(QtWidgets.QMainWindow):
    """Main user interface for the tailor app.

    The user interface centers on the table containing the data values. A single
    DataModel is instantiated to hold the data.

    """

    _selected_col_idx = None
    _plot_num = 1

    def __init__(self):
        """Initialize the class."""

        # roep de __init__() aan van de parent class
        super().__init__()

        uic.loadUi(pkg_resources.resource_stream("tailor.resources", "tailor.ui"), self)

        self.data_model = DataModel(main_window=self)
        self._set_view_and_selection_model()

        # Enable close buttons...
        self.tabWidget.setTabsClosable(True)
        # ...but remove them for the table view
        for pos in QtWidgets.QTabBar.LeftSide, QtWidgets.QTabBar.RightSide:
            widget = self.tabWidget.tabBar().tabButton(0, pos)
            if widget:
                widget.close()

        # buttons
        self.add_column_button.clicked.connect(self.add_column)
        self.add_calculated_column_button.clicked.connect(self.add_calculated_column)

        # connect menu items
        self.actionImport_CSV.triggered.connect(self.import_csv)
        self.actionExport_CSV.triggered.connect(self.export_csv)
        self.actionExport_graph.triggered.connect(self.export_graph)
        self.actionAdd_column.triggered.connect(self.add_column)
        self.actionAdd_calculated_column.triggered.connect(self.add_calculated_column)
        self.actionAdd_row.triggered.connect(self.add_row)
        self.actionRemove_column.triggered.connect(self.remove_column)
        self.actionRemove_row.triggered.connect(self.remove_row)

        # user interface events
        self.tabWidget.currentChanged.connect(self.tab_changed)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)
        self.name_edit.textEdited.connect(self.rename_column)
        self.formula_edit.textEdited.connect(self.update_column_expression)
        self.create_plot_button.clicked.connect(self.ask_and_create_plot_tab)

        # Create shortcut for return/enter keys
        for key in QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter:
            QtWidgets.QShortcut(key, self.data_view, self.edit_or_move_down)

        # Start at (0, 0)
        self.data_view.setCurrentIndex(self.data_model.createIndex(0, 0))

        # # tests
        # self.create_plot_tab("U", "I", "dU", "dI")
        # self.add_calculated_column()
        # self.name_edit.setText("P")
        # self.name_edit.textEdited.emit("P")
        # self.formula_edit.setText("U * I")
        # self.formula_edit.textEdited.emit("U * I")
        # # self.create_plot_tab("U", "Usq")
        # plot_tab = self.tabWidget.currentWidget()
        # plot_tab.fit_start_box.setValue(4.5)
        # plot_tab.fit_end_box.setValue(7.5)
        # plot_tab.use_fit_domain.setChecked(True)
        # plot_tab.model_func.setText("a * U + b")
        # plot_tab.model_func.textEdited.emit("")
        # plot_tab.fit_button.clicked.emit()
        # # plot_tab.use_fit_domain.setChecked(False)
        # # plot_tab.export_graph("test.png")
        # # plot_tab.export_graph("test.pdf")
        # # self.tabWidget.setCurrentIndex(0)
        # self.data_model._data["I"] /= 2
        # plot_tab.update_plot()
        # plot_tab.model_func.setText("a * U ** 2 + c")
        # plot_tab.model_func.textEdited.emit("")
        # self.save_project("test.tlr")
        # self.clear_all()
        # self.load_project("test.tlr")

    def _set_view_and_selection_model(self):
        self.data_view.setModel(self.data_model)
        self.data_view.setDragDropMode(self.data_view.InternalMove)

        self.selection = self.data_view.selectionModel()
        self.selection.selectionChanged.connect(self.selection_changed)

    def edit_or_move_down(self):
        """Edit cell or move cursor down a row.

        Start editing a cell. If the cell was already being edited, move the
        cursor down a row, stopping the edit in the process. Trigger a
        recalculation of all calculated columns.
        """
        cur_index = self.data_view.currentIndex()
        if not self.data_view.isPersistentEditorOpen(cur_index):
            # is not yet editing, so start an edit
            self.data_view.edit(cur_index)
        else:
            # is already editing, what index is below?
            new_index = self.get_index_below_selected_cell()
            if new_index == cur_index:
                # already on bottom row, create a new row and take that index
                self.add_row()
                new_index = self.get_index_below_selected_cell()
            # move to it (finishing editing in the process)
            self.data_view.setCurrentIndex(new_index)
            self.data_model.recalculate_all_columns()

    def get_index_below_selected_cell(self):
        """Get index directly below the selected cell."""
        return self.data_view.moveCursor(self.data_view.MoveDown, QtCore.Qt.NoModifier)

    def selection_changed(self, selected, deselected):
        """Handle selectionChanged events in the data view.

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
            if self.data_model.is_calculated_column(col_idx):
                self.formulaLabel.setEnabled(True)
                self.formula_edit.setEnabled(True)
            else:
                self.formulaLabel.setEnabled(False)
                self.formula_edit.setEnabled(False)

    def tab_changed(self, idx):
        """Handle currentChanged events of the tab widget.

        When the tab widget changes to a plot tab, update the plot to reflect
        any changes to the data that might have occured.

        Args:
            idx: an integer index of the now-focused tab.
        """
        tab = self.tabWidget.currentWidget()
        if type(tab) == PlotTab:
            tab.update_plot()

    def add_column(self):
        """Add column to data model and select it."""
        col_index = self.data_model.columnCount()
        self.data_model.insertColumn(col_index)
        self.data_view.selectColumn(col_index)

    def add_calculated_column(self):
        """Add a calculated column to data model and select it."""
        col_index = self.data_model.columnCount()
        self.data_model.insert_calculated_column(col_index)
        self.data_view.selectColumn(col_index)

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
            error_msg = QtWidgets.QMessageBox()
            error_msg.setText("You must select one or more columns.")
            error_msg.exec()

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
            error_msg = QtWidgets.QMessageBox()
            error_msg.setText("You must select one or more rows.")
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

    def update_column_expression(self, expression):
        """Update a column expression.

        Tries to recalculate the values of the currently selected column in the
        data model.

        Args:
            expression: a QString containing the mathematical expression.
        """
        if self._selected_col_idx is not None:
            self.data_model.update_column_expression(self._selected_col_idx, expression)

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

    def create_plot_tab(self, x_var, y_var, x_err=None, y_err=None):
        """Create a new tab with a plot.

        After creating the plot, the tab containing the plot is focused.

        Args:
            x_var: the name of the variable to plot on the x-axis.
            y_var: the name of the variable to plot on the y-axis.
            x_err: the name of the variable to use for the x-error bars.
            y_err: the name of the variable to use for the y-error bars.
        """
        plot_tab = PlotTab(self.data_model, main_window=self)
        idx = self.tabWidget.addTab(plot_tab, f"Plot {self._plot_num}")
        self._plot_num += 1
        plot_tab.create_plot(x_var, y_var, x_err, y_err)

        self.tabWidget.setCurrentIndex(idx)

    def create_plot_dialog(self):
        """Create a dialog to request variables for creating a plot."""
        create_dialog = QtWidgets.QDialog(parent=self)
        uic.loadUi(
            pkg_resources.resource_stream("tailor.resources", "create_plot_dialog.ui"),
            create_dialog,
        )
        choices = [None] + self.data_model.get_column_names()
        create_dialog.x_axis_box.addItems(choices)
        create_dialog.y_axis_box.addItems(choices)
        create_dialog.x_err_box.addItems(choices)
        create_dialog.y_err_box.addItems(choices)
        return create_dialog

    def close_tab(self, idx):
        """Close a plot tab.

        Closes the requested tab, but do not close the table view.

        Args:
            idx: an integer tab index
        """
        if idx > 0:
            # Don't close the table view, only close plot tabs
            self.tabWidget.removeTab(idx)

    def clear_all(self):
        """Clear all program state.

        Closes all tabs and data.
        """
        for idx in range(self.tabWidget.count(), 0, -1):
            # close all plot tabs in reverse order, they are no longer valid
            self.tabWidget.removeTab(idx)
        self._plot_num = 1
        self.data_model = DataModel(main_window=self)
        self._set_view_and_selection_model()
        self.data_view.setCurrentIndex(self.data_model.createIndex(0, 0))

    def save_project(self, filename):
        """Save a Tailor project.

        Save all data and program state (i.e. plot tabs, fit parameters, etc.)
        to a Tailor project file.

        Args:
            filename: a string containing the filename to save to.
        """
        save_obj = {
            "application": __name__,
            "version": __version__,
            "data_model": {},
            "tabs": [],
            "plot_num": self._plot_num,
            "current_tab": self.tabWidget.currentIndex(),
        }

        # save data for the data model
        self.data_model.save_state_to_obj(save_obj["data_model"])

        for idx in range(1, self.tabWidget.count()):
            # save data for each tab
            tab = self.tabWidget.widget(idx)
            tab_data = {"label": self.tabWidget.tabBar().tabText(idx)}
            tab.save_state_to_obj(tab_data)
            save_obj["tabs"].append(tab_data)

        # save data to disk
        with gzip.open(filename, "w") as f:
            f.write(json.dumps(save_obj).encode("utf-8"))

    def load_project(self, filename):
        """Load a Tailor project.

        Load all data and program state (i.e. plot tabs, fit parameters, etc.)
        from a Tailor project file.

        Args:
            filename: a string containing the filename to load from.
        """
        with gzip.open(filename) as f:
            save_obj = json.loads(f.read().decode("utf-8"))

        if save_obj["application"] == __name__:
            self.clear_all()

            # load data for the data model
            self.data_model.load_state_from_obj(save_obj["data_model"])

            # create a tab and load data for each plot
            for tab_data in save_obj["tabs"]:
                plot_tab = PlotTab(self.data_model, main_window=self)
                idx = self.tabWidget.addTab(plot_tab, tab_data["label"])
                plot_tab.load_state_from_obj(tab_data)
            self._plot_num = save_obj["plot_num"]

        self.tabWidget.setCurrentIndex(save_obj["current_tab"])

    def export_csv(self):
        """Export all data as CSV.

        Export all data in the table as a comma-separated values file.
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            filter="CSV-files (*.csv)",
            # options=QtWidgets.QFileDialog.DontUseNativeDialog,
        )
        if filename:
            self.data_model.write_csv(filename)

    def import_csv(self):
        """Import data from a CSV file.

        Erase all data and import from a comma-separated values file.
        """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            filter="CSV-files (*.csv)",
            # options=QtWidgets.QFileDialog.DontUseNativeDialog,
        )
        if filename:
            self.clear_all()
            self.data_model.read_csv(filename)
            self.data_view.setCurrentIndex(self.data_model.createIndex(0, 0))

    def export_graph(self):
        """Export a graph to a file."""
        tab = self.tabWidget.currentWidget()
        if type(tab) == PlotTab:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent=self,
                # filter="Graphics (*.png *.pdf)",
                # options=QtWidgets.QFileDialog.DontUseNativeDialog,
            )
            if filename:
                path = pathlib.Path(filename)
                if path.suffix in [".png", ".pdf"]:
                    tab.export_graph(path)
                else:
                    error_msg = QtWidgets.QMessageBox()
                    error_msg.setText("Only .png and .pdf files are supported.")
                    error_msg.exec()
        else:
            error_msg = QtWidgets.QMessageBox()
            error_msg.setText("You must select a plot tab first.")
            error_msg.exec()


def main():
    """Main entry point."""
    app = QtWidgets.QApplication(sys.argv)
    ui = UserInterface()
    ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
