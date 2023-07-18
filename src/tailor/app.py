"""Tailor app.

Import datasets or enter data by hand and create plots to explore correlations.
You can fit custom models to your data to estimate best-fit parameters.
"""

import gzip
import importlib.metadata
import json
import pathlib
import platform
import sys
import traceback
import urllib.request
import webbrowser
from functools import partial
from importlib import resources
from textwrap import dedent
from typing import Optional

import packaging
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from tailor import config, dialogs
from tailor.csv_format_dialog import (
    DELIMITER_CHOICES,
    NUM_FORMAT_CHOICES,
    CSVFormatDialog,
)
from tailor.data_sheet import DataSheet
from tailor.plot_tab import PlotTab
from tailor.ui_create_plot_dialog import Ui_CreatePlotDialog
from tailor.ui_tailor import Ui_MainWindow

metadata = importlib.metadata.metadata("tailor")
__name__ = metadata["name"]
__version__ = metadata["version"]

MAX_RECENT_FILES = 5

DIRTY_TIMEOUT = 10000  # 10 s
RELEASE_API_URL = "https://api.github.com/repos/davidfokkema/tailor/releases/latest"
HTTP_TIMEOUT = 3


# FIXME: antialiasing is EXTREMELY slow. Why?
# pg.setConfigOptions(antialias=True)
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class Application(QtWidgets.QMainWindow):
    """Main user interface for the tailor app.

    The user interface centers on the table containing the data values. A single
    DataModel is instantiated to hold the data.

    """

    _project_filename = None
    _recent_files_actions = None
    _selected_col_idx = None
    _plot_num = 1
    _sheet_num = 1

    _is_dirty = False

    def __init__(self):
        """Initialize the class."""

        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(
            QtGui.QIcon(str(resources.path("tailor.resources", "tailor.png")))
        )

        self.connect_menu_items()
        self.connect_ui_events()
        self.setup_keyboard_shortcuts()
        self.fill_recent_menu()

        # install event filter to capture UI events (which are not signals)
        # necessary to capture closeEvent inside QMainWindow widget
        self.installEventFilter(self)

        # set up dirty timer
        self._dirty_timer = QtCore.QTimer()
        self._dirty_timer.timeout.connect(self.mark_project_dirty)

        # clear all program state and set up as new project
        self.clear_all()

    def connect_menu_items(self):
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionAbout_Tailor.triggered.connect(self.show_about_dialog)
        self.ui.actionNew.triggered.connect(self.new_project)
        self.ui.actionOpen.triggered.connect(self.open_project_dialog)
        self.ui.actionSave.triggered.connect(self.save_project_or_dialog)
        self.ui.actionSave_As.triggered.connect(self.save_as_project_dialog)
        self.ui.actionCheck_for_updates.triggered.connect(self.check_for_updates)
        self.ui.actionImport_CSV.triggered.connect(self.import_csv)
        self.ui.actionExport_CSV.triggered.connect(self.export_csv)
        self.ui.actionExport_Graph_to_PDF.triggered.connect(
            lambda: self.export_graph(".pdf")
        )
        self.ui.actionExport_Graph_to_PNG.triggered.connect(
            lambda: self.export_graph(".png")
        )
        self.ui.actionClose.triggered.connect(self.new_project)
        self.ui.actionAdd_Data_Sheet.triggered.connect(self.add_data_sheet)
        self.ui.actionDuplicate_Data_Sheet.triggered.connect(self.duplicate_data_sheet)
        self.ui.actionAdd_column.triggered.connect(self.add_column)
        self.ui.actionAdd_calculated_column.triggered.connect(
            self.add_calculated_column
        )
        self.ui.actionAdd_row.triggered.connect(self.add_row)
        self.ui.actionRemove_column.triggered.connect(self.remove_column)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)
        self.ui.actionClear_Cell_Contents.triggered.connect(self.clear_selected_cells)
        self.ui.actionCopy.triggered.connect(self.copy_selected_cells)
        self.ui.actionPaste.triggered.connect(self.paste_cells)

    def connect_ui_events(self):
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)
        self.ui.tabWidget.tabCloseRequested.connect(self.close_tab)

    def setup_keyboard_shortcuts(self):
        # Set standard shortcuts for menu items
        self.ui.actionNew.setShortcut(QtGui.QKeySequence.New)
        self.ui.actionOpen.setShortcut(QtGui.QKeySequence.Open)
        self.ui.actionClose.setShortcut(QtGui.QKeySequence.Close)
        self.ui.actionSave.setShortcut(QtGui.QKeySequence.Save)
        self.ui.actionSave_As.setShortcut(QtGui.QKeySequence.SaveAs)
        self.ui.actionCopy.setShortcut(QtGui.QKeySequence.Copy)
        self.ui.actionPaste.setShortcut(QtGui.QKeySequence.Paste)

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

    def fill_recent_menu(self):
        self.ui._recent_files_separator = self.ui.menuOpen_Recent.insertSeparator(
            self.ui.actionClear_Menu
        )
        self.update_recent_files()
        self.ui.actionClear_Menu.triggered.connect(self.clear_recent_files_menu)

    def mark_project_dirty(self, is_dirty=True):
        """Mark project as dirty"""
        self._is_dirty = is_dirty
        self.update_window_title()
        if not is_dirty:
            # FIXME: this can be implemented much better by actually detecting changes.
            self._dirty_timer.start(DIRTY_TIMEOUT)

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
        if watched is self and event.type() == QtCore.QEvent.Close:
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
        box.setIconPixmap(self.windowIcon().pixmap(64, 64))
        box.setText("Tailor")
        box.setInformativeText(
            dedent(
                f"""
            <p>Version {__version__}.</p>

            <p>Tailor is written by David Fokkema for use in the physics lab courses at the Vrije Universiteit Amsterdam and the University of Amsterdam.</p>

            <p>Tailor is free software licensed under the GNU General Public License v3.0 or later.</p>

            <p>For more information, please visit:<br><a href="https://github.com/davidfokkema/tailor">https://github.com/davidfokkema/tailor</a></p>
        """
            )
        )
        box.exec()

    def _on_data_sheet(self) -> Optional[DataSheet]:
        """Return the current tab if a data sheet else display warning."""
        if type(tab := self.ui.tabWidget.currentWidget()) == DataSheet:
            return tab
        else:
            dialogs.show_warning_dialog(
                parent=self, msg="You must select a data sheet to perform this action."
            )
            return None

    def _on_plot(self) -> Optional[DataSheet]:
        """Return the current tab if it is a plot else display warning."""
        if type(tab := self.ui.tabWidget.currentWidget()) == PlotTab:
            return tab
        else:
            dialogs.show_warning_dialog(
                parent=self, msg="You must select a plot to perform this action."
            )
            return None

    def add_column(self):
        """Add a column to the current data sheet."""
        if tab := self._on_data_sheet():
            tab.add_column()

    def add_calculated_column(self):
        """Add a calculated column to the current data sheet."""
        if tab := self._on_data_sheet():
            tab.add_calculated_column()

    def add_row(self):
        """Add a row to the current data sheet."""
        if tab := self._on_data_sheet():
            tab.add_row()

    def remove_column(self):
        """Remove a column from the current data sheet."""
        if tab := self._on_data_sheet():
            tab.remove_column()

    def remove_row(self):
        """Remove a row from the current data sheet."""
        if tab := self._on_data_sheet():
            tab.remove_row()

    def clear_selected_cells(self):
        """Clear the contents of selected cells in the current data sheet."""
        if tab := self._on_data_sheet():
            tab.clear_selected_cells()

    def copy_selected_cells(self):
        """Copy selected cells in the current data sheet."""
        if tab := self._on_data_sheet():
            tab.copy_selected_cells()

    def paste_cells(self):
        """Paste selected cells into the current data sheet."""
        if tab := self._on_data_sheet():
            tab.paste_cells()

    def tab_changed(self, idx):
        """Handle currentChanged events of the tab widget.

        When the tab widget changes to a plot tab, update the plot to reflect
        any changes to the data that might have occured.

        Args:
            idx: an integer index of the now-focused tab.
        """
        self.update_plot_tab(idx)

    def update_plot_tab(self, idx):
        """Update plot tab.

        Update the plot to reflect any changes to the data that might have
        occured.

        Args:
            idx: an integer index of the tab.
        """
        tab = self.ui.tabWidget.widget(idx)
        if type(tab) == PlotTab:
            tab.refresh_ui()

    def update_all_plots(self):
        """Update all plot tabs.

        Update all plots to reflect any changes to the data that might have
        occured.
        """
        for idx in range(self.ui.tabWidget.count()):
            self.update_plot_tab(idx)

    def rename_plot_variables(self, data_sheet, old_name, new_name):
        """Rename any plotted variables

        Args:
            data_sheet (DataSheet): the data sheet containing the column that
                needs to be renamed.
            old_name (str): the name that may be currently in use.
            new_name (str): the new column name.
        """
        num_tabs = self.ui.tabWidget.count()
        tabs = [self.ui.tabWidget.widget(i) for i in range(num_tabs)]
        for tab in tabs:
            if type(tab) == PlotTab and tab.data_sheet == data_sheet:
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

    def ask_and_create_plot_tab(self):
        """Opens a dialog and create a new tab with a plot.

        First, a create plot dialog is opened to query the user for the columns
        to plot. When the dialog is accepted, creates a new tab containing the
        requested plot.
        """
        if data_sheet := self._on_data_sheet():
            dialog = self.create_plot_dialog(data_sheet)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                labels = [None] + data_sheet.data_model.columnLabels()
                x_var = labels[dialog.ui.x_axis_box.currentIndex()]
                y_var = labels[dialog.ui.y_axis_box.currentIndex()]
                x_err = labels[dialog.ui.x_err_box.currentIndex()]
                y_err = labels[dialog.ui.y_err_box.currentIndex()]
                print(f"{x_var=} {y_var=} {x_err=} {y_err=}")
                if x_var and y_var:
                    self.create_plot_tab(data_sheet, x_var, y_var, x_err, y_err)

    def create_plot_tab(
        self, data_sheet, x_var, y_var, x_err=None, y_err=None
    ) -> PlotTab:
        """Create a new tab with a plot.

        After creating the plot, the tab containing the plot is focused.

        Args:
            data_sheet (DataSheet): the sheet containing the data.
            x_var: the name of the variable to plot on the x-axis.
            y_var: the name of the variable to plot on the y-axis.
            x_err: the name of the variable to use for the x-error bars.
            y_err: the name of the variable to use for the y-error bars.
        """
        plot_tab = PlotTab(data_sheet, x_var, y_var, x_err, y_err)
        idx = self.ui.tabWidget.addTab(plot_tab, f"Plot {self._plot_num}")
        self._plot_num += 1
        self.ui.tabWidget.setCurrentIndex(idx)
        return plot_tab

    def create_plot_dialog(self, data_sheet: DataSheet) -> QtWidgets.QDialog:
        """Create a dialog to request variables for creating a plot."""

        class Dialog(QtWidgets.QDialog):
            def __init__(self):
                super().__init__()
                self.ui = Ui_CreatePlotDialog()
                self.ui.setupUi(self)

        choices = [None] + data_sheet.data_model.columnNames()
        create_dialog = Dialog()
        create_dialog.ui.x_axis_box.addItems(choices)
        create_dialog.ui.y_axis_box.addItems(choices)
        create_dialog.ui.x_err_box.addItems(choices)
        create_dialog.ui.y_err_box.addItems(choices)
        return create_dialog

    def close_tab(self, close_idx):
        """Close a tab.

        Closes the requested tab. If it is a data sheet, close all related plots.

        Args:
            close_idx: an integer tab index
        """
        tab_widget = self.ui.tabWidget
        close_tab = tab_widget.widget(close_idx)
        if type(close_tab) == PlotTab:
            # plots can be easily closed
            if self.confirm_close_dialog("Are you sure you want to close this plot?"):
                tab_widget.removeTab(close_idx)
        elif type(close_tab) == DataSheet:
            # data sheets need special attention
            if self.confirm_close_dialog(
                "Are you sure you want to close this data sheet and all associated plots?"
            ):
                if self._count_data_sheets() == 1:
                    # there's just the one data sheet, close all and start new
                    # project
                    self.clear_all()
                else:
                    # find associated plots and close plots and data sheet
                    close_idxs = [close_idx]
                    for idx in range(tab_widget.count()):
                        tab = tab_widget.widget(idx)
                        if (
                            type(tab) == PlotTab
                            and tab.data_model == close_tab.data_model
                        ):
                            close_idxs.append(idx)
                    for idx in sorted(close_idxs, reverse=True):
                        tab_widget.removeTab(idx)

    def _count_data_sheets(self):
        """Count the number of data sheets."""
        is_data_sheet = [
            type(self.ui.tabWidget.widget(idx)) == DataSheet
            for idx in range(self.ui.tabWidget.count())
        ]
        return sum(is_data_sheet)

    def clear_all(self):
        """Clear all program state.

        Closes all tabs and data.
        """
        self.ui.tabWidget.clear()
        self.ui.tabWidget.setTabsClosable(True)

        self._plot_num = 1
        self._sheet_num = 1
        self.add_data_sheet()
        self._set_project_path(None)
        self.mark_project_dirty(False)

    def add_data_sheet(self) -> DataSheet:
        """Add a new data sheet to the project."""
        name = f"Sheet{self._sheet_num}"
        datasheet = DataSheet(name, main_window=self)
        idx = self.ui.tabWidget.addTab(datasheet, name)
        self.ui.tabWidget.setCurrentIndex(idx)
        datasheet.ui.data_view.setFocus()
        self._sheet_num += 1
        return datasheet

    def duplicate_data_sheet(self) -> DataSheet:
        """Duplicate the current data sheet."""
        if current_sheet := self._on_data_sheet():
            new_sheet = self.add_data_sheet()
            new_sheet.data_model.beginResetModel()
            new_sheet.data_model._data = current_sheet.data_model._data.copy(deep=True)
            new_sheet.data_model.endResetModel()

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
            parent=self,
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
                tab = self.ui.tabWidget.widget(idx)
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

        self.update_recent_files(filename)
        self.mark_project_dirty(False)

    def open_project_dialog(self):
        """Present open project dialog and load project."""
        if self.confirm_project_close_dialog():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                parent=self,
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
                self,
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
            self,
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
                    self.ui.tabWidget.addTab(plot_tab, tab_data["label"])
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
        if data_sheet := self._on_data_sheet():
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent=self,
                dir=self.get_recent_directory(),
                filter="CSV files (*.csv);;Text files (*.txt);;All files (*)",
            )
            if filename:
                self._do_export_csv(data_sheet, filename)

    def _do_export_csv(self, data_sheet, filename):
        """Export sheet data as CSV.

        Args:
            data_sheet (DataSheet): the data sheet containing the data.
            filename (str or pathlib.Path): the filename to save the data to.
        """
        self.set_recent_directory(pathlib.Path(filename).parent)
        data_sheet.data_model.write_csv(filename)

    def import_csv(self):
        """Import data from a CSV file.

        After confirmation, erase all data and import from a comma-separated
        values file.
        """
        if data_sheet := self._on_data_sheet():
            if self.confirm_project_close_dialog():
                filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                    parent=self,
                    dir=self.get_recent_directory(),
                    filter="CSV files (*.csv);;Text files (*.txt);;All files (*)",
                )
                if filename:
                    self.set_recent_directory(pathlib.Path(filename).parent)
                    dialog = CSVFormatDialog(filename, parent=self)
                    if dialog.exec() == QtWidgets.QDialog.Accepted:
                        (
                            delimiter,
                            decimal,
                            thousands,
                            header,
                            skiprows,
                        ) = dialog.get_format_parameters()
                        self._do_import_csv(
                            data_sheet,
                            filename,
                            delimiter,
                            decimal,
                            thousands,
                            header,
                            skiprows,
                        )

    def _do_import_csv(
        self, data_sheet, filename, delimiter, decimal, thousands, header, skiprows
    ):
        """Import CSV data from file.

        Args:
            data_sheet (DataSheet): the data sheet into which the data will be
                written.
            filename: a string containing the path to the CSV file
            delimiter: a string containing the column delimiter
            decimal: a string containing the decimal separator
            thousands: a string containing the thousands separator
            header: an integer with the row number containing the column names,
                or None.
            skiprows: an integer with the number of rows to skip at start of file
        """
        if data_sheet.data_model.is_empty():
            # when the data only contains empty cells, overwrite all columns
            import_func = data_sheet.data_model.read_csv
        else:
            import_func = data_sheet.data_model.read_and_concat_csv

        import_func(
            filename,
            delimiter=delimiter,
            decimal=decimal,
            thousands=thousands,
            header=header,
            skiprows=skiprows,
        )
        data_sheet.ui.data_view.setCurrentIndex(data_sheet.data_model.createIndex(0, 0))
        self.update_all_plots()

    def export_graph(self, suffix):
        """Export a graph to a file.

        If the user specifies a name with a different suffix an error will be
        displayed.

        Args:
            suffix: the required suffix of the file.
        """
        if tab := self._on_plot():
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent=self,
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
                    dialogs.show_error_dialog(
                        self, f"You didn't select a {suffix} file."
                    )

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
        self.setWindowTitle(title)

    def _show_exception(self, exc, title, text):
        """Show a messagebox with detailed exception information.

        Args:
            exc: the exception.
            title: short header text.
            text: longer informative text describing the problem.
        """
        msg = QtWidgets.QMessageBox(parent=self)
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

    def check_for_updates(self, silent=False):
        """Check for new releases of Tailor.

        Args:
            silent (bool, optional): If there are no updates available, should
                this method return silently? Defaults to False.
        """
        (
            latest_version,
            update_link,
            release_notes_link,
        ) = self.get_latest_version_and_update_link()
        if latest_version is None:
            msg = "You appear to have no internet connection or GitHub is down."
        elif update_link is None:
            msg = f"You appear to be on the latest version ({__version__}), great!"
        else:
            msg = dedent(
                f"""\
                <p>There is a new version available. You have version {__version__} and the latest
                version is {latest_version}. You can download the new version using the link below.</p>

                <p><a href={release_notes_link}>Release notes</a></p>
                <p></p>
                """
            )
        if silent and update_link is None:
            # no updates, and asked to be silent
            return
        elif update_link is None:
            dialog = QtWidgets.QMessageBox(parent=self)
            dialog.setText("Updates")
            dialog.setInformativeText(msg)
            dialog.setStyleSheet("QLabel{min-width: 300px;}")
            dialog.setStandardButtons(dialog.Ok)
            dialog.exec()
        else:
            dialog = QtWidgets.QMessageBox(parent=self)
            dialog.setText("Updates")
            dialog.setInformativeText(msg)
            dialog.setStyleSheet("QLabel{min-width: 300px;}")
            dialog.setStandardButtons(dialog.Ok | dialog.Cancel)

            dialog.button(dialog.Ok).setText("Download Update")
            dialog.button(dialog.Cancel).setText("Skip Update")

            value = dialog.exec()
            match value:
                case dialog.Ok:
                    # if app is in the main event loop, ask to quit so user can
                    # install update
                    QtWidgets.QApplication.instance().quit()
                    # after possible 'save your project' dialogs, download update
                    webbrowser.open(update_link)
                    # if not, return with True to signal that the user wants the update
                    return True
                case dialog.Cancel:
                    return False
                case default:
                    return None

    def get_latest_version_and_update_link(self):
        """Get latest version and link to latest release, if available.

        Get the latest version of Tailor. If a new release is available, returns
        a platform-specific download link. If there is no new release, returns
        None.

        Returns:
            str: URL to download link or None.
        """
        try:
            r = urllib.request.urlopen(RELEASE_API_URL, timeout=HTTP_TIMEOUT)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            # no internet connection?
            return None, None, None
        else:
            release_info = json.loads(r.read())
            latest_version = release_info["name"]
            if packaging.version.parse(latest_version) > packaging.version.parse(
                __version__
            ):
                asset_urls = [a["browser_download_url"] for a in release_info["assets"]]
                system, machine = platform.system(), platform.machine()
                try:
                    match system, machine:
                        case ("Darwin", "arm64"):
                            download_url = next(
                                (u for u in asset_urls if "apple_silicon.dmg" in u),
                                None,
                            ) or next(u for u in asset_urls if ".dmg" in u)
                        case ("Darwin", "x86_64"):
                            download_url = next(
                                (u for u in asset_urls if "intel.dmg" in u), None
                            ) or next(u for u in asset_urls if ".dmg" in u)
                        case ("Windows", *machine):
                            download_url = next(u for u in asset_urls if ".msi" in u)
                        case default:
                            # platform not yet supported
                            download_url = None
                except StopIteration:
                    # the iterator in the next()-statement was empty, so no updates available
                    download_url = None
            else:
                # No new version available
                download_url = None
            return latest_version, download_url, release_info["html_url"]


def main():
    """Main entry point."""
    qapp = QtWidgets.QApplication()
    app = Application()
    app.show()
    # Preflight
    if not "--no-update-check" in sys.argv:
        # will check for updates
        if app.check_for_updates(silent=True):
            # user wants to install available updates, so quit
            return
    sys.exit(qapp.exec())


if __name__ == "__main__":
    main()
