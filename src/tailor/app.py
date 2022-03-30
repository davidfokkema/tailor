"""Tailor app.

Import datasets or enter data by hand and create plots to explore correlations.
You can fit custom models to your data to estimate best-fit parameters.
"""

import gzip
import json
import pathlib
import sys
import traceback
from functools import partial
from importlib import metadata as importlib_metadata
from importlib import resources
from textwrap import dedent

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtUiTools import QUiLoader

from tailor import config
from tailor.csv_format_dialog import (
    DELIMITER_CHOICES,
    NUM_FORMAT_CHOICES,
    CSVFormatDialog,
)
from tailor.data_model import MSG_TIMEOUT, DataModel
from tailor.plot_tab import PlotTab

app_module = sys.modules["__main__"].__package__
metadata = importlib_metadata.metadata(app_module)
__name__ = metadata["name"]
__version__ = metadata["version"]


MAX_RECENT_FILES = 5

DIRTY_TIMEOUT = 10000  # 10 s


# FIXME: antialiasing is EXTREMELY slow. Why?
# pg.setConfigOptions(antialias=True)
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class Application(QtCore.QObject):
    """Main user interface for the tailor app.

    The user interface centers on the table containing the data values. A single
    DataModel is instantiated to hold the data.

    """

    _project_filename = None
    _recent_files_actions = None
    _selected_col_idx = None
    _plot_num = 1

    _is_dirty = False

    def __init__(self):
        """Initialize the class."""

        super().__init__()

        self.ui = QUiLoader().load(resources.path("tailor.resources", "tailor.ui"))
        self.ui.setWindowIcon(
            QtGui.QIcon(str(resources.path("tailor.resources", "tailor.png")))
        )
        # store reference to this code in data tab
        self.ui.data.code = self

        self.clear_all()

        # Enable close buttons...
        self.ui.tabWidget.setTabsClosable(True)
        # ...but remove them for the table view
        for pos in QtWidgets.QTabBar.LeftSide, QtWidgets.QTabBar.RightSide:
            widget = self.ui.tabWidget.tabBar().tabButton(0, pos)
            if widget:
                widget.close()

        # connect button signals
        self.ui.add_column_button.clicked.connect(self.add_column)
        self.ui.add_calculated_column_button.clicked.connect(self.add_calculated_column)

        # connect menu items
        self.ui.actionQuit.triggered.connect(self.ui.close)
        self.ui.actionAbout_Tailor.triggered.connect(self.show_about_dialog)
        self.ui.actionNew.triggered.connect(self.new_project)
        self.ui.actionOpen.triggered.connect(self.open_project_dialog)
        self.ui.actionSave.triggered.connect(self.save_project_or_dialog)
        self.ui.actionSave_As.triggered.connect(self.save_as_project_dialog)
        self.ui.actionImport_CSV.triggered.connect(
            lambda: self.import_csv(create_new=True)
        )
        self.ui.actionImport_CSV_Into_Current_Project.triggered.connect(
            lambda: self.import_csv(create_new=False)
        )
        self.ui.actionExport_CSV.triggered.connect(self.export_csv)
        self.ui.actionExport_Graph_to_PDF.triggered.connect(
            lambda: self.export_graph(".pdf")
        )
        self.ui.actionExport_Graph_to_PNG.triggered.connect(
            lambda: self.export_graph(".png")
        )
        self.ui.actionClose.triggered.connect(self.new_project)
        self.ui.actionAdd_column.triggered.connect(self.add_column)
        self.ui.actionAdd_calculated_column.triggered.connect(
            self.add_calculated_column
        )
        self.ui.actionAdd_row.triggered.connect(self.add_row)
        self.ui.actionRemove_column.triggered.connect(self.remove_column)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)
        self.ui.actionClear_Cell_Contents.triggered.connect(self.clear_selected_cells)

        # set up the open recent menu
        self.ui._recent_files_separator = self.ui.menuOpen_Recent.insertSeparator(
            self.ui.actionClear_Menu
        )
        self.update_recent_files()
        self.ui.actionClear_Menu.triggered.connect(self.clear_recent_files_menu)

        # user interface events
        self.ui.data_view.horizontalHeader().sectionMoved.connect(self.column_moved)
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)
        self.ui.tabWidget.tabCloseRequested.connect(self.close_tab)
        self.ui.name_edit.textEdited.connect(self.rename_column)
        self.ui.formula_edit.textEdited.connect(self.update_column_expression)
        self.ui.create_plot_button.clicked.connect(self.ask_and_create_plot_tab)

        # install event filter to capture UI events (which are not signals)
        # necessary to caputer closeEvent inside QMainWindow widget
        self.ui.installEventFilter(self)

        # Set standard shortcuts for menu items
        self.ui.actionNew.setShortcut(QtGui.QKeySequence.New)
        self.ui.actionOpen.setShortcut(QtGui.QKeySequence.Open)
        self.ui.actionClose.setShortcut(QtGui.QKeySequence.Close)
        self.ui.actionSave.setShortcut(QtGui.QKeySequence.Save)
        self.ui.actionSave_As.setShortcut(QtGui.QKeySequence.SaveAs)

        # Set other shortcuts for menu items
        self.ui.actionImport_CSV.setShortcut(QtGui.QKeySequence("Ctrl+I"))
        self.ui.actionImport_CSV_Into_Current_Project.setShortcut(
            QtGui.QKeySequence("Shift+Ctrl+I")
        )
        self.ui.actionExport_CSV.setShortcut(QtGui.QKeySequence("Ctrl+E"))
        self.ui.actionExport_Graph_to_PDF.setShortcut(QtGui.QKeySequence("Ctrl+G"))
        self.ui.actionExport_Graph_to_PNG.setShortcut(
            QtGui.QKeySequence("Shift+Ctrl+G")
        )

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

        # Start at (0, 0)
        self.ui.data_view.setCurrentIndex(self.data_model.createIndex(0, 0))

        # tests
        # filename = "~/Desktop/meting1.csv"
        # dialog = CSVFormatDialog(filename)
        # dialog.exec()
        # sys.exit()
        # if dialog.exec() == QtWidgets.QDialog.Accepted:
        #     (
        #         delimiter,
        #         decimal,
        #         thousands,
        #         header,
        #         skiprows,
        #     ) = dialog.get_format_parameters()
        #     self._do_import_csv(
        #         filename, delimiter, decimal, thousands, header, skiprows
        #     )
        # self._do_import_csv(filename, ";", ",", ".", 0, 0)

        # import numpy as np
        # import pandas as pd

        # x = [1, 2, 3, 4, 5, np.nan]
        # y = [1, 4, np.nan, 8, 10, np.nan]
        # self.data_model.beginResetModel()
        # self.data_model._data = pd.DataFrame.from_dict({"x": x, "y": y})
        # self.data_model.endResetModel()
        # self.create_plot_tab("x", "y")
        # plot_tab = self.ui.tabWidget.currentWidget()
        # plot_tab.model_func.setText("a * x + b")
        # plot_tab.fit_button.clicked.emit()

        # np.random.seed(1)
        # x = np.linspace(0, 10, 11)
        # y = np.random.normal(loc=x, scale=0.1 * x, size=len(x))
        # self.data_model.beginResetModel()
        # self.data_model._data = pd.DataFrame.from_dict(
        #     {"U": x, "I": y, "dU": 0.1 * x + 0.01, "dI": 0.1 * y + 0.01}
        # )
        # self.data_model.endResetModel()
        # self.create_plot_tab("U", "I", "dU", "dI")

        # plot_tab = self.tabWidget.currentWidget()
        # plot_tab.model_func.setText("U0 * U + b")
        # plot_tab.fit_button.clicked.emit()

        # plot_tab.model_func.setText("(U0 * U + b")
        # plot_tab.fit_button.clicked.emit()

        # self.tabWidget.setCurrentIndex(0)
        # self.data_view.selectColumn(0)
        # self.name_edit.setText("U_0")
        # self.name_edit.textEdited.emit("U_0")
        # self.data_view.selectColumn(1)
        # self.name_edit.setText("I_0")
        # self.name_edit.textEdited.emit("I_0")
        # self.tabWidget.setCurrentIndex(1)
        # plot_tab.fit_button.clicked.emit()

        # self.add_calculated_column()
        # self.name_edit.setText("inv_U")
        # self.formula_edit.setText("1 / U")
        # self.create_plot_tab("inv_U", "I")

        # self.add_calculated_column()
        # self.name_edit.setText("P")
        # self.formula_edit.setText("U * I")
        # self.name_edit.textEdited.emit("P")
        # self.formula_edit.textEdited.emit("U * I")
        # self.data_view.selectColumn(0)
        # self.remove_column()
        # self.add_column()
        # self.name_edit.setText("P")
        # self.data_view.selectColumn(0)
        # # self.create_plot_tab("U", "Usq")
        # plot_tab = self.tabWidget.currentWidget()
        # # plot_tab.fit_start_box.setValue(4.5)
        # # plot_tab.fit_end_box.setValue(7.5)
        # # plot_tab.use_fit_domain.setChecked(True)
        # plot_tab.model_func.setText("a * U + b")
        # # for row in plot_tab._params.values():
        # #     row.itemAt(plot_tab._idx_value_box).widget().setValue(20)
        # plot_tab.fit_button.clicked.emit()
        # plot_tab.draw_curve_option.setCurrentIndex(2)
        # # plot_tab.use_fit_domain.setChecked(False)
        # # plot_tab.export_graph("test.png")
        # # plot_tab.export_graph("test.pdf")
        # # self.tabWidget.setCurrentIndex(0)
        # # self.data_model._data["I"] /= 2
        # # plot_tab.update_plot()
        # # plot_tab.model_func.setText("a * U ** 2 + c")
        # # plot_tab.model_func.textEdited.emit("")
        # self.save_project("test.tlr")
        # self.clear_all()
        # self.load_project(pathlib.Path.home() / "Desktop" / "analyse-radon220.tlr")
        # self.save_project("test.tlr")
        # self.clear_all()
        # self.load_project("test.tlr")

        # self._do_import_csv(
        #     "~/Desktop/importtest.csv", ",", ".", ",", 0, 0, create_new=False
        # )

    def _set_view_and_selection_model(self):
        self.ui.data_view.setModel(self.data_model)
        self.ui.data_view.setDragDropMode(self.ui.data_view.NoDragDrop)
        header = self.ui.data_view.horizontalHeader()
        header.setSectionsMovable(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setMinimumSectionSize(header.defaultSectionSize())

        self.selection = self.ui.data_view.selectionModel()
        self.selection.selectionChanged.connect(self.selection_changed)

    def mark_project_dirty(self, is_dirty=True):
        """Mark project as dirty"""
        self._is_dirty = is_dirty
        self.update_window_title()
        if not is_dirty:
            # FIXME: this can be implemented much better by actually detecting changes.
            QtCore.QTimer.singleShot(DIRTY_TIMEOUT, self.mark_project_dirty)

    def column_moved(self, logidx, oldidx, newidx):
        """Move column in reaction to UI signal.

        Dragging a column to a new location triggers execution of this method.
        Since the UI only reorders the column visually and does not change the
        underlying data, we will store the ordering in the data model.

        Args:
            logidx (int): the logical column index (index in the dataframe)
            oldidx (int): the old visual index
            newidx (int): the new visual index
        """
        self.data_model._column_order = self.get_column_ordering()
        self.data_model.recalculate_all_columns()

    def get_column_ordering(self):
        """Return the logical order of columns in the table view."""
        header = self.ui.data_view.horizontalHeader()
        n_columns = len(self.data_model.get_column_names())
        return [header.logicalIndex(i) for i in range(n_columns)]

    def eventFilter(self, watched, event):
        """Catch PySide6 events.

        Events are signals without slots. That is, signals which cannot be
        connected to predefined endpoints. They can, however, be captured by an
        event filter.

        Args:
            watched (QtCore.QObject): the object which generated the event.
            event (QtCore.QEvent): the event object.

        Returns:
            boolean: True if the event is ignored, False otherwise.
        """
        if watched is self.ui and event.type() == QtCore.QEvent.Close:
            if self.confirm_project_close_dialog():
                event.accept()
                return False
            else:
                event.ignore()
                return True
        else:
            return super().eventFilter(watched, event)

    def show_about_dialog(self):
        """Show about application dialog."""
        box = QtWidgets.QMessageBox()
        box.setIconPixmap(self.ui.windowIcon().pixmap(64, 64))
        box.setText("Tailor")
        box.setInformativeText(
            dedent(
                f"""
            Version {__version__}.

            Tailor is written by David Fokkema for use in the physics lab courses at the Vrije Universiteit Amsterdam and the University of Amsterdam.

            Tailor is free software licensed under the GNU General Public License v3.0 or later.
        """
            )
        )
        box.exec()

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
            self.data_model.setData(index, "")

    def get_index_below_selected_cell(self):
        """Get index directly below the selected cell."""
        return self.ui.data_view.moveCursor(
            self.ui.data_view.MoveDown, QtCore.Qt.NoModifier
        )

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
            self.ui.nameLabel.setEnabled(True)
            self.ui.name_edit.setEnabled(True)
            first_selection = selected.first()
            col_idx = first_selection.left()
            self._selected_col_idx = col_idx
            self.ui.name_edit.setText(self.data_model.get_column_name(col_idx))
            self.ui.formula_edit.setText(self.data_model.get_column_expression(col_idx))
            if self.data_model.is_calculated_column(col_idx):
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

    def tab_changed(self, idx):
        """Handle currentChanged events of the tab widget.

        When the tab widget changes to a plot tab, update the plot to reflect
        any changes to the data that might have occured.

        Args:
            idx: an integer index of the now-focused tab.
        """
        tab = self.ui.tabWidget.currentWidget().code
        if type(tab) == PlotTab:
            tab.update_plot()

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
        self.data_model.insert_calculated_column(col_index)
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
            # Do not allow empty names or duplicate column names
            if name and name not in self.data_model.get_column_names():
                old_name = self.data_model.get_column_name(self._selected_col_idx)
                new_name = self.data_model.rename_column(self._selected_col_idx, name)
                self.rename_plot_variables(old_name, new_name)
                # set the normalized name to the name edit field
                self.ui.name_edit.setText(new_name)

    def rename_plot_variables(self, old_name, new_name):
        """Rename any plotted variables

        Args:
            old_name: the name that may be currently in use.
            new_name: the new column name
        """
        num_tabs = self.ui.tabWidget.count()
        tabs = [self.ui.tabWidget.widget(i).code for i in range(num_tabs)]
        for tab in tabs:
            if type(tab) == PlotTab:
                needs_info_update = False
                for var in ["x_var", "y_var", "x_err_var", "y_err_var"]:
                    if getattr(tab, var) == old_name:
                        needs_info_update = True
                        setattr(tab, var, new_name)
                        # The following creates problems with partial matches
                        # For now, the model function is *not* updated
                        #
                        # if var == "x_var":
                        # update model expression and model object
                        # expr = tab.model_func.text()
                        # new_expr = expr.replace(old_name, new_name)
                        # tab.model_func.setText(new_expr)
                        # tab.get_params_and_update_model()
                        if var == "y_var":
                            # update y-label for model expression
                            tab.update_function_label(new_name)
                if needs_info_update:
                    tab.update_info_box()

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
        plot_tab = PlotTab(self.data_model, main_app=self)
        idx = self.ui.tabWidget.addTab(plot_tab.ui, f"Plot {self._plot_num}")
        self._plot_num += 1
        plot_tab.create_plot(x_var, y_var, x_err, y_err)

        self.ui.tabWidget.setCurrentIndex(idx)

    def create_plot_dialog(self):
        """Create a dialog to request variables for creating a plot."""
        create_dialog = QUiLoader().load(
            resources.path("tailor.resources", "create_plot_dialog.ui"),
            self.ui,
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
            if self.confirm_close_dialog("Are you sure you want to close this plot?"):
                self.ui.tabWidget.removeTab(idx)

    def clear_all(self):
        """Clear all program state.

        Closes all tabs and data.
        """
        for idx in range(self.ui.tabWidget.count(), 0, -1):
            # close all plot tabs in reverse order, they are no longer valid
            self.ui.tabWidget.removeTab(idx)
        self._plot_num = 1
        self.data_model = DataModel(main_app=self)
        self._set_view_and_selection_model()
        self.ui.data_view.setCurrentIndex(self.data_model.createIndex(0, 0))
        self._set_project_path(None)
        self.mark_project_dirty(False)

    def new_project(self):
        """Close the current project and open a new one."""
        if self.confirm_project_close_dialog():
            self.clear_all()

    def save_project_or_dialog(self):
        """Save project or present a dialog.

        When you first save a project, present a dialog to select a filename. If
        you previously opened or saved this project, just save it without
        presenting the dialog.
        """
        if self._project_filename is None:
            self.save_as_project_dialog()
        else:
            self.save_project(self._project_filename)

    def save_as_project_dialog(self):
        """Present save project dialog and save project."""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self.ui,
            dir=self.get_recent_directory(),
            filter="Tailor project files (*.tlr);;All files (*)",
        )
        if filename:
            self.set_recent_directory(pathlib.Path(filename).parent)
            self.save_project(filename)

    def save_project(self, filename):
        """Save a Tailor project.

        Save all data and program state (i.e. plot tabs, fit parameters, etc.)
        to a Tailor project file.

        Args:
            filename: a string containing the filename to save to.
        """
        try:
            save_obj = {
                "application": __name__,
                "version": __version__,
                "data_model": {},
                "tabs": [],
                "plot_num": self._plot_num,
                "current_tab": self.ui.tabWidget.currentIndex(),
            }

            # save data for the data model
            self.data_model.save_state_to_obj(save_obj["data_model"])

            for idx in range(1, self.ui.tabWidget.count()):
                # save data for each tab
                tab = self.ui.tabWidget.widget(idx).code
                tab_data = {"label": self.ui.tabWidget.tabBar().tabText(idx)}
                tab.save_state_to_obj(tab_data)
                save_obj["tabs"].append(tab_data)
        except Exception as exc:
            self._show_exception(
                exc,
                title="Unable to save project.",
                text="This is a bug in the application.",
            )

        # save data to disk
        with gzip.open(filename, "w") as f:
            f.write(json.dumps(save_obj).encode("utf-8"))

        # remember filename for subsequent call to "Save"
        self._set_project_path(filename)

    def open_project_dialog(self):
        """Present open project dialog and load project."""
        if self.confirm_project_close_dialog():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                parent=self.ui,
                dir=self.get_recent_directory(),
                filter="Tailor project files (*.tlr);;All files (*)",
            )
            if filename:
                self.set_recent_directory(pathlib.Path(filename).parent)
                self.load_project(filename)

    def get_recent_directory(self):
        """Get recent directory from config file.

        Returns:
            str: the most recently visited directory.
        """
        cfg = config.read_config()
        return cfg.get("recent_dir", None)

    def set_recent_directory(self, directory):
        """Save the most recently visited directory to the config file.

        Args:
            directory (str or pathlib.Path): the most recently visited directory.
        """
        cfg = config.read_config()
        cfg["recent_dir"] = str(directory)
        config.write_config(cfg)

    def confirm_project_close_dialog(self):
        """Present a confirmation dialog before closing a project.

        Present a dialog to confirm that the user really wants to close a
        project and lose possible changes.

        Returns:
            A boolean. If True, the user confirms closing the project. If False,
            the user wants to cancel the action.
        """
        if not self._is_dirty:
            # There are no changes, skip confirmation dialog
            return True
        else:
            msg = "This action will lose any changes in the current project. Discard the current project, or cancel?"
            button = QtWidgets.QMessageBox.warning(
                self.ui,
                "Please confirm",
                msg,
                buttons=QtWidgets.QMessageBox.Save
                | QtWidgets.QMessageBox.Discard
                | QtWidgets.QMessageBox.Cancel,
                defaultButton=QtWidgets.QMessageBox.Cancel,
            )
            if button == QtWidgets.QMessageBox.Discard:
                return True
            elif button == QtWidgets.QMessageBox.Save:
                self.save_project_or_dialog()
                return True
            else:
                return False

    def confirm_close_dialog(self, msg=None):
        """Present a confirmation dialog before closing.

        Present a dialog to confirm that the user really wants to close an
        object and lose possible changes.

        Args:
            msg: optional message to present to the user. If None, the default
                message asks for confirmation to discard the current project.

        Returns:
            A boolean. If True, the user confirms closing the project. If False,
            the user wants to cancel the action.
        """
        if msg is None:
            msg = "You might lose changes."
        button = QtWidgets.QMessageBox.warning(
            self.ui,
            "Please confirm",
            msg,
            buttons=QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Cancel,
            defaultButton=QtWidgets.QMessageBox.Cancel,
        )
        if button == QtWidgets.QMessageBox.Close:
            return True
        else:
            return False

    def load_project(self, filename):
        """Load a Tailor project.

        Load all data and program state (i.e. plot tabs, fit parameters, etc.)
        from a Tailor project file.

        Args:
            filename: a string containing the filename to load from.
        """
        try:
            with gzip.open(filename) as f:
                save_obj = json.loads(f.read().decode("utf-8"))

            if save_obj["application"] == __name__:
                self.clear_all()

                # remember filename for subsequent call to "Save"
                self._set_project_path(filename)

                # load data for the data model
                self.data_model.load_state_from_obj(save_obj["data_model"])

                # create a tab and load data for each plot
                for tab_data in save_obj["tabs"]:
                    plot_tab = PlotTab(self.data_model, main_app=self)
                    self.ui.tabWidget.addTab(plot_tab.ui, tab_data["label"])
                    plot_tab.load_state_from_obj(tab_data)
                self._plot_num = save_obj["plot_num"]
                self.ui.tabWidget.setCurrentIndex(save_obj["current_tab"])
        except Exception as exc:
            self._show_exception(
                exc,
                title="Unable to open project.",
                text="This can happen if the file is corrupt or if there is a bug in the application.",
            )
        else:
            self.update_recent_files(filename)
            self.mark_project_dirty(False)
            self.ui.statusbar.showMessage(
                "Finished loading project.", timeout=MSG_TIMEOUT
            )

    def export_csv(self):
        """Export all data as CSV.

        Export all data in the table as a comma-separated values file.
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self.ui,
            dir=self.get_recent_directory(),
            filter="CSV files (*.csv);;Text files (*.txt);;All files (*)",
        )
        if filename:
            self.set_recent_directory(pathlib.Path(filename).parent)
            self.data_model.write_csv(filename)

    def import_csv(self, create_new=True):
        """Import data from a CSV file.

        After confirmation, erase all data and import from a comma-separated
        values file.

        Args:
            create_new: a boolean indicating whether or not to create a new
                project or import into the existing project.
        """
        if self.confirm_project_close_dialog():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                parent=self.ui,
                dir=self.get_recent_directory(),
                filter="CSV files (*.csv);;Text files (*.txt);;All files (*)",
            )
            if filename:
                self.set_recent_directory(pathlib.Path(filename).parent)
                dialog = CSVFormatDialog(filename, parent=self.ui)
                if dialog.ui.exec() == QtWidgets.QDialog.Accepted:
                    (
                        delimiter,
                        decimal,
                        thousands,
                        header,
                        skiprows,
                    ) = dialog.get_format_parameters()
                    self._do_import_csv(
                        filename,
                        delimiter,
                        decimal,
                        thousands,
                        header,
                        skiprows,
                        create_new,
                    )

    def _do_import_csv(
        self, filename, delimiter, decimal, thousands, header, skiprows, create_new=True
    ):
        """Import CSV data from file.

        Args:
            filename: a string containing the path to the CSV file
            delimiter: a string containing the column delimiter
            decimal: a string containing the decimal separator
            thousands: a string containing the thousands separator
            header: an integer with the row number containing the column names,
                or None.
            skiprows: an integer with the number of rows to skip at start of file
            create_new: a boolean indicating whether or not to create a new
                project or import into the existing project.
        """
        if create_new:
            self.clear_all()
            import_func = self.data_model.read_csv
        else:
            import_func = self.data_model.read_and_concat_csv

        import_func(
            filename,
            delimiter=delimiter,
            decimal=decimal,
            thousands=thousands,
            header=header,
            skiprows=skiprows,
        )
        self.ui.data_view.setCurrentIndex(self.data_model.createIndex(0, 0))

    def export_graph(self, suffix):
        """Export a graph to a file.

        If the user specifies a name with a different suffix an error will be
        displayed.

        Args:
            suffix: the required suffix of the file.
        """
        tab = self.ui.tabWidget.currentWidget().code
        if type(tab) == PlotTab:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent=self.ui,
                dir=self.get_recent_directory(),
                filter=f"Graphics (*{suffix});;All files (*)",
            )
            if filename:
                path = pathlib.Path(filename)
                self.set_recent_directory(path.parent)
                if path.suffix == suffix:
                    try:
                        tab.export_graph(path)
                    except Exception as exc:
                        self._show_exception(
                            exc,
                            title="Unable to export graph.",
                            text="This can happen if there is a bug in the application.",
                        )
                else:
                    error_msg = QtWidgets.QMessageBox()
                    error_msg.setText(f"You didn't select a {suffix} file.")
                    error_msg.exec()
        else:
            error_msg = QtWidgets.QMessageBox()
            error_msg.setText("You must select a plot tab first.")
            error_msg.exec()

    def _set_project_path(self, filename):
        """Set window title and project name."""
        self._project_filename = filename
        self.update_window_title()

    def update_window_title(self):
        """Update window title.

        Include project name and dirty flag in the title.
        """
        filename = self._project_filename
        title = "Tailor"
        if filename is not None:
            title += f": {pathlib.Path(filename).stem}"
        if self._is_dirty:
            title += "*"
        self.ui.setWindowTitle(title)

    def _show_exception(self, exc, title, text):
        """Show a messagebox with detailed exception information.

        Args:
            exc: the exception.
            title: short header text.
            text: longer informative text describing the problem.
        """
        msg = QtWidgets.QMessageBox(parent=self.ui)
        msg.setText(title)
        msg.setInformativeText(text)
        msg.setDetailedText(traceback.format_exc())
        msg.setStyleSheet("QLabel{min-width: 400px;}")
        msg.exec()

    def update_recent_files(self, file=None):
        """Update open recent files list.

        Update open recent files list in menu and in configuration file.

        Args:
            file (pathlib.Path or str): the most recent file which will be added to the list.
        """
        cfg = config.read_config()
        recents = cfg.get("recent_files", [])
        if file:
            path = str(file)
            if path in recents:
                recents.remove(path)
            recents.insert(0, path)
            recents = recents[:MAX_RECENT_FILES]
            cfg["recent_files"] = recents
            config.write_config(cfg)
        self.populate_recent_files_menu(recents)

    def populate_recent_files_menu(self, recents):
        """Populate the open recent files menu.

        Populate the recent files with a list of recent file names.

        Args:
            recents (list): A list of recent file names.
        """
        if self._recent_files_actions:
            for action in self._recent_files_actions:
                self.ui.menuOpen_Recent.removeAction(action)
        if recents:
            actions = [QtGui.QAction(f) for f in recents]
            self.ui.menuOpen_Recent.insertActions(
                self.ui._recent_files_separator, actions
            )
            for action in actions:
                action.triggered.connect(
                    partial(self.open_recent_project_action, action.text())
                )
            self.ui.actionClear_Menu.setEnabled(True)
            self._recent_files_actions = actions

    def clear_recent_files_menu(self):
        """Clear the open recent files menu."""
        for action in self._recent_files_actions:
            self.ui.menuOpen_Recent.removeAction(action)
        self._recent_files_actions = None
        cfg = config.read_config()
        cfg["recent_files"] = []
        config.write_config(cfg)
        self.ui.actionClear_Menu.setEnabled(False)

    def open_recent_project_action(self, filename):
        if self.confirm_project_close_dialog():
            self.load_project(filename)


def main():
    """Main entry point."""
    qapp = QtWidgets.QApplication(sys.argv)
    app = Application()
    app.ui.show()
    sys.exit(qapp.exec())


if __name__ == "__main__":
    main()
