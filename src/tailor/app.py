"""Tailor app.

Import datasets or enter data by hand and create plots to explore correlations.
You can fit custom models to your data to estimate best-fit parameters.
"""

import importlib.metadata
import json
import pathlib
import platform
import sys
import tempfile
import urllib.request
import webbrowser
from functools import partial
from importlib import resources
from textwrap import dedent
from typing import NamedTuple, Optional

import click
import packaging
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from tailor import config, dialogs, project_files
from tailor.csv_format_dialog import (
    DELIMITER_CHOICES,
    NUM_FORMAT_CHOICES,
    CSVFormatDialog,
    FormatParameters,
)
from tailor.data_sheet import DataSheet
from tailor.data_source_dialog import DataSourceDialog
from tailor.multiplot_tab import MultiPlotTab
from tailor.plot_tab import PlotTab
from tailor.ui_create_plot_dialog import Ui_CreatePlotDialog
from tailor.ui_preview_dialog import Ui_PreviewDialog
from tailor.ui_rename_dialog import Ui_RenameDialog
from tailor.ui_tailor import Ui_MainWindow

metadata = importlib.metadata.metadata("tailor")
__name__ = metadata["name"]
__version__ = metadata["version"]


class TabbedWidget(NamedTuple):
    widget: DataSheet | PlotTab | MultiPlotTab
    index: int


MAX_RECENT_FILES = 5

RELEASE_API_URL = "https://api.github.com/repos/davidfokkema/tailor/releases/latest"
HTTP_TIMEOUT = 3

TAILOR_PROJECT_FILTER = "Tailor project files (*.tlr);;All files (*)"
CSV_FILE_FILTER = "CSV files (*.csv);;Text files (*.txt);;All files (*)"

pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class MainWindow(QtWidgets.QMainWindow):
    """Main user interface for the tailor app.

    The user interface centers on the table containing the data values. A single
    DataModel is instantiated to hold the data.

    """

    _project_filename = None
    _recent_files_actions = None
    _selected_col_idx = None
    _plot_num: int
    _sheet_num: int

    _is_dirty = False

    def __init__(self, add_sheet=False):
        """Initialize the class."""

        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(
            QtGui.QIcon(str(resources.files("tailor.resources") / "tailor.png"))
        )

        self.connect_menu_items()
        self.connect_ui_events()
        self.setup_keyboard_shortcuts()
        self.fill_recent_menu()

        # install event filter to capture UI events (which are not signals)
        # necessary to capture closeEvent inside QMainWindow widget
        self.installEventFilter(self)

        # clear all program state and set up as new project
        self.clear_all(add_sheet)

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
        self.ui.actionPreview_Graph.triggered.connect(self.preview_graph)
        self.ui.actionExport_Graph_to_PDF.triggered.connect(
            lambda: self.export_graph(".pdf")
        )
        self.ui.actionExport_Graph_to_PNG.triggered.connect(
            lambda: self.export_graph(".png")
        )
        self.ui.actionClose.triggered.connect(self.new_project)
        # use lambda to gobble 'checked' parameter
        self.ui.actionAdd_Data_Sheet.triggered.connect(lambda: self.add_data_sheet())
        self.ui.actionDuplicate_Data_Sheet.triggered.connect(self.duplicate_data_sheet)
        self.ui.actionDuplicate_Data_Sheet_With_Plots.triggered.connect(
            self.duplicate_data_sheet_with_plots
        )
        self.ui.actionCreate_Plot.triggered.connect(self.ask_and_create_plot_tab)
        self.ui.actionDuplicate_Plot.triggered.connect(self.duplicate_plot)
        self.ui.actionCreate_MultiPlot.triggered.connect(self.create_multiplot)
        self.ui.actionChange_Plot_Source.triggered.connect(self.change_plot_data_source)
        self.ui.actionRename_Data_Sheet.triggered.connect(self.rename_data_sheet)
        self.ui.actionRename_Plot.triggered.connect(self.rename_plot)

        self.ui.actionAdd_column.triggered.connect(self.add_column)
        self.ui.actionAdd_calculated_column.triggered.connect(
            self.add_calculated_column
        )
        self.ui.actionAdd_row.triggered.connect(self.add_row)
        self.ui.actionRemove_column.triggered.connect(self.remove_selected_columns)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)
        self.ui.actionClear_Cell_Contents.triggered.connect(self.clear_selected_cells)
        self.ui.actionCopy.triggered.connect(self.copy_selected_cells)
        self.ui.actionPaste.triggered.connect(self.paste_cells)

    def connect_ui_events(self):
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)
        self.ui.tabWidget.tabCloseRequested.connect(self.close_tab_with_children)

    def setup_keyboard_shortcuts(self):
        # Set standard shortcuts for menu items
        self.ui.actionNew.setShortcut(QtGui.QKeySequence.New)
        self.ui.actionOpen.setShortcut(QtGui.QKeySequence.Open)
        self.ui.actionClose.setShortcut(QtGui.QKeySequence.Close)
        self.ui.actionSave.setShortcut(QtGui.QKeySequence.Save)
        self.ui.actionSave_As.setShortcut(QtGui.QKeySequence.SaveAs)
        self.ui.actionCopy.setShortcut(QtGui.QKeySequence.Copy)
        self.ui.actionPaste.setShortcut(QtGui.QKeySequence.Paste)
        self.ui.actionPreview_Graph.setShortcut(QtGui.QKeySequence.Print)

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
        """Mark project as dirty or as clean."""
        self._is_dirty = is_dirty
        self.update_window_title()

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

    def _on_plot(self) -> Optional[PlotTab]:
        """Return the current tab if it is a plot else display warning."""
        if type(tab := self.ui.tabWidget.currentWidget()) == PlotTab:
            return tab
        else:
            dialogs.show_warning_dialog(
                parent=self, msg="You must select a plot to perform this action."
            )
            return None

    def _on_plot_or_multiplot(self) -> Optional[PlotTab | MultiPlotTab]:
        """Return the current tab if it is a plot else display warning."""
        if type(tab := self.ui.tabWidget.currentWidget()) in (PlotTab, MultiPlotTab):
            return tab
        else:
            dialogs.show_warning_dialog(
                parent=self,
                msg="You must select a plot or multiplot to perform this action.",
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

    def remove_selected_columns(self):
        """Remove a column from the current data sheet."""
        msgs = []
        if current_tab := self._on_data_sheet():
            selected_labels = current_tab.get_selected_column_labels()

            # find associated plots
            plot_titles = self.get_plots_which_use_columns(current_tab, selected_labels)
            if plot_titles:
                titles = [f"'{plot}'" for plot in plot_titles]
                msgs.append(f"This column is used by plots {', '.join(titles)}.")

            # find associated calculated columns
            column_names = self.get_columns_which_use_columns(
                current_tab, selected_labels
            )
            if column_names:
                names = [f"'{col}'" for col in column_names]
                msgs.append(
                    f"This column is used by calculated columns {', '.join(names)}."
                )

            if msgs:
                msgs.insert(
                    0,
                    "This column can only be removed when it is unused. Please remove the following items first.",
                )
                dialogs.show_warning_dialog(parent=self, msg=" ".join(msgs))
            else:
                current_tab.remove_selected_columns()

    def get_plots_which_use_columns(
        self, sheet: DataSheet, columns: list[str]
    ) -> list[str]:
        """Get plot titles which use one of the supplied columns.

        Check which plots use one of the supplied columns and return their
        titles. This method should be called with the column _labels_, not their
        _names_.

        Args:
            sheet (DataSheet): the DataSheet containing the columns.
            columns (list[str]): a list of column labels.

        Returns:
            list[str]: a list of plot titles that use one of the columns.
        """
        data_model = sheet.model.data_model
        plot_titles = []
        for idx in range(self.ui.tabWidget.count()):
            tab = self.ui.tabWidget.widget(idx)
            if type(tab) == PlotTab and tab.model.uses(data_model, columns):
                plot_titles.append(tab.name)
        return plot_titles

    def get_columns_which_use_columns(
        self, sheet: DataSheet, columns: list[str]
    ) -> list[str]:
        """Get column names which use any of the supplied columns.

        Check which columns use any of the supplied other columns and return
        their names. This method should be called with the column _labels_, not
        their _names_. Only checks other columns, so if 'b' uses 'a', and we ask
        'who uses a or b', do _not_ return 'b'.

        Args:
            sheet (DataSheet): the DataSheet containing the columns.
            columns (list[str]): a list of column labels.

        Returns:
            list[str]: a list of column names which use any of the columns.
        """
        column_names = []
        for idx in range(sheet.model.columnCount()):
            # only check other columns
            if sheet.model.columnLabel(idx) not in columns:
                if sheet.model.columnUses(idx, columns):
                    column_names.append(sheet.model.columnName(idx))
        return column_names

    def remove_row(self):
        """Remove a row from the current data sheet."""
        if tab := self._on_data_sheet():
            tab.remove_selected_row()

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
        if type(tab) == PlotTab or type(tab) == MultiPlotTab:
            tab.refresh_ui()

    def ask_and_create_plot_tab(self):
        """Opens a dialog and create a new tab with a plot.

        First, a create plot dialog is opened to query the user for the columns
        to plot. When the dialog is accepted, creates a new tab containing the
        requested plot.
        """
        if data_sheet := self._on_data_sheet():
            dialog = self.create_plot_dialog(data_sheet)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                labels = [None] + data_sheet.model.columnLabels()
                x_var = labels[dialog.ui.x_axis_box.currentIndex()]
                y_var = labels[dialog.ui.y_axis_box.currentIndex()]
                x_err = labels[dialog.ui.x_err_box.currentIndex()]
                y_err = labels[dialog.ui.y_err_box.currentIndex()]
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
        self._plot_num += 1
        name = f"Plot {self._plot_num}"
        plot_tab = PlotTab(
            main_window=self,
            name=name,
            id=self._plot_num,
            data_sheet=data_sheet,
            x_col=x_var,
            y_col=y_var,
            x_err_col=x_err,
            y_err_col=y_err,
        )
        idx = self.ui.tabWidget.addTab(plot_tab, name)
        self.ui.tabWidget.setCurrentIndex(idx)
        self.mark_project_dirty()
        return plot_tab

    def add_plot_tab(self, plot_tab: PlotTab) -> None:
        """Create a new tab for the supplied plot.

        Args:
            plot_tab (PlotTab): the plot for which to create a new tab.
        """
        self._plot_num += 1
        # create fresh plot id
        plot_tab.id = self._plot_num
        idx = self.ui.tabWidget.addTab(plot_tab, plot_tab.name)
        self.ui.tabWidget.setCurrentIndex(idx)
        self.mark_project_dirty()

    def create_plot_dialog(self, data_sheet: DataSheet) -> QtWidgets.QDialog:
        """Create a dialog to request variables for creating a plot."""

        class Dialog(QtWidgets.QDialog):
            def __init__(self):
                super().__init__()
                self.ui = Ui_CreatePlotDialog()
                self.ui.setupUi(self)

        choices = [None] + data_sheet.model.columnNames()
        create_dialog = Dialog()
        create_dialog.ui.x_axis_box.addItems(choices)
        create_dialog.ui.y_axis_box.addItems(choices)
        create_dialog.ui.x_err_box.addItems(choices)
        create_dialog.ui.y_err_box.addItems(choices)
        return create_dialog

    def close_tab_with_children(self, close_idx):
        """Close a tab.

        Closes the requested tab with all children (related plots and
        multiplots).

        Args:
            close_idx: an integer tab index
        """
        close_tab = TabbedWidget(
            widget=self.ui.tabWidget.widget(close_idx), index=close_idx
        )
        if type(close_tab.widget) == DataSheet:
            # data sheets need special attention
            if self._count_data_sheets() == 1:
                # there's just the one data sheet, close all and start new
                # project
                if self.confirm_close_dialog(
                    "Are you sure you want to close the only data sheet and start a new project?"
                ):
                    self.clear_all(add_sheet=True)
            else:
                tabs = self.get_associated_tabs(close_tab)
                plot_titles = [p.widget.name for p in tabs]
                if self.confirm_close_dialog(
                    f"Are you sure you want to close this data sheet and all associated plots ({', '.join(plot_titles)})?"
                ):
                    self.close_tabs([close_tab] + tabs)
        elif type(close_tab.widget) == PlotTab:
            tabs = self.get_associated_tabs(close_tab)
            multiplot_titles = [p.widget.name for p in tabs]
            if self.confirm_close_dialog(
                f"Are you sure you want to close this plot and associated multiplots ({', '.join(multiplot_titles)})?"
            ):
                self.close_tabs([close_tab] + tabs)
        elif type(close_tab.widget) == MultiPlotTab:
            if self.confirm_close_dialog("Are you sure you want to close this plot?"):
                self.close_tabs([close_tab])

    def get_associated_tabs(self, tab: TabbedWidget) -> list[TabbedWidget]:
        """Get all tabs associated with a data sheet or plot.

        Args:
            tab (TabbedWidget): the tab for which to get associated tabs.

        Raises:
            NotImplementedError: only implemented for DataSheet and PlotTab.

        Returns:
            list[TabbedWidget]: a list of associated tabs.
        """
        if type(tab.widget) == DataSheet:
            # find associated plots
            plots = self.get_associated_plots(tab.widget)
        elif type(tab.widget) == PlotTab:
            plots = [tab]
        else:
            raise NotImplementedError(
                f"Associated tabs for type {type(tab)} not implemented."
            )
        multiplots = []
        for plot in plots:
            multiplots.extend(self.get_associated_multiplots(plot.widget))
        return plots + multiplots

    def close_tabs(self, tabs: list[TabbedWidget]) -> None:
        """Close tabs using a list of tabbed widgets.

        Args:
            close_idxs (list[TabbedWidget]): a list of tabbed widgets (sheets,
                plots or multiplots).
        """
        close_idxs = [t.index for t in tabs]
        # close from right to left to avoid jumping indexes
        for idx in sorted(close_idxs, reverse=True):
            self.ui.tabWidget.removeTab(idx)
        self.mark_project_dirty()

    def get_associated_plots(self, data_sheet: DataSheet) -> list[TabbedWidget]:
        """Get plots associated with a data sheet."""
        plots = []
        for idx in range(self.ui.tabWidget.count()):
            tab = self.ui.tabWidget.widget(idx)
            if type(tab) == PlotTab and tab.data_sheet == data_sheet:
                plots.append(TabbedWidget(index=idx, widget=tab))
        return plots

    def get_associated_multiplots(self, plot: PlotTab) -> list[TabbedWidget]:
        """Get multiplots associated with a plot."""
        multiplots = []
        for idx in range(self.ui.tabWidget.count()):
            tab = self.ui.tabWidget.widget(idx)
            if type(tab) == MultiPlotTab and tab.model.uses_plot(plot):
                multiplots.append(TabbedWidget(index=idx, widget=tab))
        return multiplots

    def get_data_sheets(self) -> list[DataSheet]:
        """Get a list of the data sheets.

        Returns:
            list[DataSheet]: a list of all data sheets
        """
        widgets = [
            self.ui.tabWidget.widget(idx) for idx in range(self.ui.tabWidget.count())
        ]
        return [widget for widget in widgets if type(widget) == DataSheet]

    def get_plots(self) -> list[PlotTab]:
        """Get a list of all plots.

        Returns:
            list[PlotTab]: a list of all plots.
        """
        widgets = [
            self.ui.tabWidget.widget(idx) for idx in range(self.ui.tabWidget.count())
        ]
        return [widget for widget in widgets if type(widget) == PlotTab]

    def _count_data_sheets(self):
        """Count the number of data sheets."""
        is_data_sheet = [
            type(self.ui.tabWidget.widget(idx)) == DataSheet
            for idx in range(self.ui.tabWidget.count())
        ]
        return sum(is_data_sheet)

    def clear_all(self, add_sheet=False):
        """Clear all program state.

        Closes all tabs and data, optionally creating a new empty data sheet.

        Args:
            add_sheet (bool, optional): Should add a new data sheet be added.
                Defaults to False.
        """
        self.ui.tabWidget.clear()
        self.ui.tabWidget.setTabsClosable(True)

        self._plot_num = 0
        self._sheet_num = 0
        self._set_project_path(None)
        if add_sheet:
            sheet = self.add_data_sheet()
            sheet.model.renameColumn(0, "x")
            sheet.model.renameColumn(1, "y")
            # force updating column information in UI
            sheet.selection_changed()
        self.mark_project_dirty(False)

    def add_data_sheet(self, new_sheet: DataSheet | None = None) -> DataSheet:
        """Add a new data sheet to the project.

        If a data sheet is supplied, that one is added as a new sheet.

        Args:
            new_sheet (DataSheet | None, optional): a prebuilt data sheet.
                Defaults to None.

        Returns:
            DataSheet: the newly added data sheet.
        """
        self._sheet_num += 1
        name = f"Sheet {self._sheet_num}"
        if new_sheet is None:
            new_sheet = DataSheet(name=name, id=self._sheet_num, main_window=self)
        else:
            new_sheet.name = name
            new_sheet.id = self._sheet_num
        idx = self.ui.tabWidget.addTab(new_sheet, name)
        self.ui.tabWidget.setCurrentIndex(idx)
        new_sheet.ui.data_view.setFocus()
        self.mark_project_dirty()
        return new_sheet

    def duplicate_data_sheet(self) -> None:
        """Duplicate the current data sheet.

        The data sheet is duplicated by leveraging code used to managing project
        files.
        """
        if current_sheet := self._on_data_sheet():
            model = project_files.save_data_sheet(current_sheet)
            new_sheet = project_files.load_data_sheet(app=self, model=model)
            self.add_data_sheet(new_sheet)

    def duplicate_data_sheet_with_plots(self) -> None:
        """Duplicate the current data sheet and associated plots.

        The data sheet and plots are duplicated by leveraging code used to managing project
        files. The plots use the new data sheet as the data source.
        """
        if current_sheet := self._on_data_sheet():
            model = project_files.save_data_sheet(current_sheet)
            new_sheet = project_files.load_data_sheet(app=self, model=model)
            self.add_data_sheet(new_sheet)
            idx = self.ui.tabWidget.currentIndex()
            for plot in self.get_associated_plots(current_sheet):
                model = project_files.save_plot(plot.widget)
                model.name += f" ({new_sheet.name})"
                new_plot = project_files.load_plot(
                    project=self, model=model, data_sheet=new_sheet
                )
                self.add_plot_tab(new_plot)
            self.ui.tabWidget.setCurrentIndex(idx)

    def duplicate_plot(self) -> None:
        """Duplicate the current plot.

        The plot is duplicated by leveraging code used to managing project files.
        """
        if current_plot := self._on_plot():
            model = project_files.save_plot(current_plot)
            model.name = f"Plot {self._plot_num + 1}"
            new_plot = project_files.load_plot(
                project=self, model=model, data_sheet=current_plot.data_sheet
            )
            self.add_plot_tab(new_plot)

    def create_multiplot(self) -> MultiPlotTab | None:
        if plot := self._on_plot():
            name = f"Plot {self._plot_num + 1}"
            multiplot = MultiPlotTab(
                main_window=self,
                name=name,
                id=-1,
                x_label=plot.model.x_label,
                y_label=plot.model.y_label,
            )
            multiplot.add_plot(plot)
            self.add_plot_tab(multiplot)
            return multiplot

    def change_plot_data_source(self) -> None:
        """Change the data source of a plot.

        When you've added a plot to Sheet 1 and you want to have the same plot
        for Sheet 2, first duplicate the plot and then change the data source to
        Sheet 2.
        """
        if plot := self._on_plot():
            data_sheets = self.get_data_sheets()
            dialog = DataSourceDialog(plot, data_sheets)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                x_col_name = dialog.ui.x_box.currentText()
                y_col_name = dialog.ui.y_box.currentText()
                if x_col_name == "" or y_col_name == "":
                    dialogs.show_warning_dialog(
                        parent=self, msg="You must select both x and y axes."
                    )
                else:
                    x_err_col_name = dialog.ui.x_err_box.currentText()
                    y_err_col_name = dialog.ui.y_err_box.currentText()
                    plot.change_data_source(
                        data_sheet=data_sheets[
                            dialog.ui.data_source_box.currentIndex()
                        ],
                        x_col_name=x_col_name,
                        x_err_col_name=x_err_col_name,
                        y_col_name=y_col_name,
                        y_err_col_name=y_err_col_name,
                    )

    def rename_data_sheet(self) -> None:
        if sheet := self._on_data_sheet():
            self._do_rename_widget(sheet)

    def rename_plot(self) -> None:
        if plot := self._on_plot_or_multiplot():
            self._do_rename_widget(plot)

    def _do_rename_widget(self, widget) -> None:
        class Dialog(QtWidgets.QDialog):
            def __init__(self):
                super().__init__()
                self.ui = Ui_RenameDialog()
                self.ui.setupUi(self)

        dialog = Dialog()
        dialog.ui.name_box.setText(widget.name)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            widget.name = dialog.ui.name_box.text()
            tab_idx = self.ui.tabWidget.indexOf(widget)
            self.ui.tabWidget.setTabText(tab_idx, widget.name)

    def new_project(self):
        """Close the current project and open a new one."""
        if self.confirm_project_close_dialog():
            self.clear_all(add_sheet=True)

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
        filename = self.get_save_filename_dialog(filter=TAILOR_PROJECT_FILTER)
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
            project_files.save_project_to_path(self, filename)
        except Exception as exc:
            dialogs.show_exception(
                parent=self,
                exc=exc,
                title="Unable to save project.",
                text="This is a bug in the application.",
            )
        else:
            # remember filename for subsequent call to "Save"
            self._set_project_path(filename)

            self.update_recent_files(filename)
            self.mark_project_dirty(False)

    def open_project_dialog(self, event=None, filename=None):
        """Present open project dialog and load project."""
        if self.confirm_project_close_dialog():
            if filename is None:
                filename = self.get_open_filename_dialog(filter=TAILOR_PROJECT_FILTER)
            if filename:
                self.set_recent_directory(pathlib.Path(filename).parent)
                self.load_project(filename)

    def get_open_filename_dialog(self, filter):
        """Get a filename from a 'Open File' dialog.

        Args:
            filter (str): available options for filtering filenames

        Returns:
            str|None: path to the file or None.
        """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            dir=self.get_recent_directory(),
            filter=filter,
        )

        return filename

    def get_save_filename_dialog(self, filter):
        """Get a filename from a 'Save File' dialog.

        Args:
            filter (str): available options for filtering filenames

        Returns:
            str|None: path to the file or None.
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            dir=self.get_recent_directory(),
            filter=filter,
        )
        return filename

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
            self.clear_all()
            project_files.load_project_from_path(self, filename)
        except Exception as exc:
            dialogs.show_exception(
                parent=self,
                exc=exc,
                title="Unable to open project.",
                text="This can happen if the file is corrupt or if there is a bug in the application.",
            )
        else:
            # remember filename for subsequent call to "Save"
            self._set_project_path(filename)
            self.update_recent_files(filename)
            # rebuild UI on all tabs
            current_idx = self.ui.tabWidget.currentIndex()
            for idx in range(self.ui.tabWidget.count()):
                self.ui.tabWidget.setCurrentIndex(idx)
            self.ui.tabWidget.setCurrentIndex(current_idx)
            # mark project as not dirty (clean)
            self.mark_project_dirty(False)

    def export_csv(self):
        """Export all data as CSV.

        Export all data in the table as a comma-separated values file.
        """
        if data_sheet := self._on_data_sheet():
            filename = self.get_save_filename_dialog(filter=CSV_FILE_FILTER)
            if filename:
                self.set_recent_directory(pathlib.Path(filename).parent)
                data_sheet.model.export_csv(filename)

    def import_csv(self):
        """Import data from a CSV file.

        After confirmation, erase all data and import from a comma-separated
        values file.
        """
        if data_sheet := self._on_data_sheet():
            if (
                not data_sheet.model.is_empty()
                and not self.confirm_project_close_dialog()
            ):
                return
            else:
                print(f"{data_sheet.model.is_empty()=}")
                filename = self.get_open_filename_dialog(filter=CSV_FILE_FILTER)
                if filename:
                    self.set_recent_directory(pathlib.Path(filename).parent)
                    dialog = CSVFormatDialog(filename, parent=self)
                    if dialog.exec() == QtWidgets.QDialog.Accepted:
                        format_parameters = dialog.get_format_parameters()
                        self._do_import_csv(data_sheet, filename, format_parameters)

    def _do_import_csv(
        self, data_sheet: DataSheet, filename: str, format: FormatParameters
    ) -> None:
        """Import CSV data from file.

        Args:
            data_sheet (DataSheet): the data sheet into which the data will be
                written.
            filename: a string containing the path to the CSV file
            format (FormatParameters): CSV format parameters
        """
        if data_sheet.model.is_empty():
            # when the data only contains empty cells, overwrite all columns
            data_sheet.model.import_csv(filename, format)
        else:
            data_sheet.model.merge_csv(filename, format)
        data_sheet.ui.data_view.setCurrentIndex(data_sheet.model.createIndex(0, 0))

    def preview_graph(self):
        if plot := self._on_plot_or_multiplot():

            class Dialog(QtWidgets.QDialog):
                def __init__(self):
                    super().__init__()
                    self.ui = Ui_PreviewDialog()
                    self.ui.setupUi(self)

            with tempfile.NamedTemporaryFile(delete=False) as file:
                try:
                    plot.export_graph(file, dpi=100)
                except Exception as exc:
                    dialogs.show_exception(
                        parent=self,
                        exc=exc,
                        title="Unable to preview graph.",
                        text="It might help to check your axis labels for invalid LaTeX code.",
                    )
                else:
                    dialog = Dialog()
                    pixmap = QtGui.QPixmap()
                    pixmap.load(file.name)
                    dialog.ui.label.setPixmap(pixmap)
                    dialog.exec()
                    # delete must be False on Windows, so remove manually
                    file.close()
                    pathlib.Path(file.name).unlink()

    def export_graph(self, suffix):
        """Export a graph to a file.

        If the user specifies a name with a different suffix an error will be
        displayed.

        Args:
            suffix: the required suffix of the file.
        """
        if plot := self._on_plot_or_multiplot():
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
                        plot.export_graph(path)
                    except Exception as exc:
                        dialogs.show_exception(
                            parent=self,
                            exc=exc,
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
        if not pathlib.Path(filename).is_file():
            dialogs.show_error_dialog(parent=self, msg="File does not exist.")
        else:
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
            dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
            dialog.exec()
        else:
            dialog = QtWidgets.QMessageBox(parent=self)
            dialog.setText("Updates")
            dialog.setInformativeText(msg)
            dialog.setStyleSheet("QLabel{min-width: 300px;}")
            dialog.setStandardButtons(
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
            )

            dialog.button(QtWidgets.QMessageBox.Ok).setText("Download Update")
            dialog.button(QtWidgets.QMessageBox.Cancel).setText("Skip Update")

            value = dialog.exec()
            match value:
                case QtWidgets.QMessageBox.Ok:
                    # if app is in the main event loop, ask to quit so user can
                    # install update
                    QtWidgets.QApplication.instance().quit()
                    # after possible 'save your project' dialogs, download update
                    webbrowser.open(update_link)
                    # if not, return with True to signal that the user wants the update
                    return True
                case QtWidgets.QMessageBox.Cancel:
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


class Application(QtWidgets.QApplication):
    def __init__(
        self, project_path: str | None = None, update_check: bool = True
    ) -> None:
        super().__init__()

        self.app = MainWindow(add_sheet=True)
        self.app.show()
        # Preflight
        if update_check:
            # will check for updates
            if self.app.check_for_updates(silent=True):
                # user wants to install available updates, so quit
                return
        if project_path and pathlib.Path(project_path).is_file():
            self.app.open_project_dialog(filename=project_path)

    def event(self, event):
        if event.type() == QtCore.QEvent.FileOpen:
            self.app.open_project_dialog(filename=event.file())
            return True
        return super().event(event)


@click.command()
@click.argument("project_path", required=False)
@click.option(
    "--update-check/--no-update-check", default=True, help="Check for new versions."
)
def main(project_path, update_check):
    """Application for fitting non-linear models to experimental data.

    The path to a project file to open on launch can be supplied as an argument.
    """
    qapp = Application(project_path, update_check)
    sys.exit(qapp.exec())


if __name__ == "__main__":
    main()
