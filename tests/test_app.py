import numpy as np
import pytest
from PySide6 import QtCore, QtWidgets
from pytest_mock import MockerFixture

from tailor.app import MainWindow, dialogs
from tailor.data_sheet import DataSheet
from tailor.multiplot_tab import MultiPlotTab
from tailor.plot_tab import DRAW_CURVE_OPTIONS, DrawCurve, PlotTab


@pytest.fixture()
def data_sheet(mocker: MockerFixture) -> DataSheet:
    sheet = DataSheet(name="Sheet 2", id=1234, main_window=mocker.Mock())
    sheet.model.setDataFromArray(
        sheet.model.createIndex(0, 0),
        np.array(
            [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [float("nan"), 1.0, 4.0, 9.0, 16.0, 25.0]]
        ).T,
    )
    sheet.model.insertCalculatedColumn(2)
    sheet.model.insertCalculatedColumn(3)
    sheet.model.insertCalculatedColumn(4)
    sheet.model.insertCalculatedColumn(5)
    sheet.model.insertCalculatedColumn(6)
    sheet.model.renameColumn(0, "x")
    sheet.model.renameColumn(1, "y")
    sheet.model.renameColumn(2, "z")
    sheet.model.renameColumn(3, "yerr")
    sheet.model.renameColumn(4, "empty")
    sheet.model.renameColumn(5, "position")
    sheet.model.renameColumn(6, "use_pos")
    sheet.model.updateColumnExpression(2, "0.02 * x ** 2")
    sheet.model.updateColumnExpression(3, "0.1")
    sheet.model.updateColumnExpression(5, "0.5 * x ** 2 + y * z")
    sheet.model.updateColumnExpression(6, "position")
    return sheet


@pytest.fixture()
def simple_data_sheet(mocker: MockerFixture) -> DataSheet:
    sheet = DataSheet(name="Sheet 3", id=2345, main_window=mocker.MagicMock())
    sheet.model.setDataFromArray(
        sheet.model.createIndex(0, 0),
        np.array(
            [[1.0, 3.0, 5.0, 7.0, 9.0], [0.0, 1.0, 2.0, 3.0, 4.0], 5 * [0.1], 5 * [0.2]]
        ).T,
    )
    sheet.model.renameColumn(0, "pos")
    sheet.model.renameColumn(1, "t")
    sheet.model.renameColumn(2, "err_pos")
    sheet.model.renameColumn(3, "err_t")
    return sheet


@pytest.fixture()
def plot_tab(data_sheet: DataSheet, mocker: MockerFixture) -> PlotTab:
    plot_tab = PlotTab(
        main_window=mocker.Mock(),
        name="Plot 1",
        id=12345,
        data_sheet=data_sheet,
        x_col="col1",
        y_col="col2",
        x_err_col="col3",
        y_err_col="col4",
    )
    plot_tab.model.x_label = "Time"
    plot_tab.model.y_label = "Distance"
    plot_tab.model.update_model_expression("a * x + b")
    plot_tab.model._parameters["a"].value = 2.0
    plot_tab.model.perform_fit()
    option = DrawCurve.ON_DOMAIN
    option_idx = list(DRAW_CURVE_OPTIONS.keys()).index(option)
    plot_tab.ui.draw_curve_option.setCurrentIndex(option_idx)
    return plot_tab


@pytest.fixture()
def simple_project_without_plot(data_sheet: DataSheet) -> MainWindow:
    project = MainWindow(add_sheet=True)
    project.ui.tabWidget.addTab(data_sheet, data_sheet.name)
    project._sheet_num += 1
    return project


@pytest.fixture()
def simple_project(
    simple_project_without_plot: MainWindow, plot_tab: PlotTab
) -> MainWindow:
    project = simple_project_without_plot
    project.ui.tabWidget.addTab(plot_tab, plot_tab.name)
    project._plot_num += 1
    return project


@pytest.fixture()
def project_with_two_sheets(
    simple_project: MainWindow, simple_data_sheet: DataSheet
) -> MainWindow:
    project = simple_project
    project.ui.tabWidget.addTab(simple_data_sheet, simple_data_sheet.name)
    project._sheet_num += 1
    return project


@pytest.fixture()
def project_with_multiplot(simple_project: MainWindow) -> MainWindow:
    project = simple_project
    multiplot_tab = create_multiplot_tab(
        parent=project, plot_tab=simple_project.ui.tabWidget.widget(2)
    )
    project.ui.tabWidget.addTab(multiplot_tab, multiplot_tab.name)
    project._plot_num += 1
    return project


def create_multiplot_tab(parent: MainWindow, plot_tab: PlotTab) -> MultiPlotTab:
    multiplot_tab = MultiPlotTab(
        main_window=parent,
        name="Multiplot 1",
        id=45678,
        x_label="Time",
        y_label="Distance",
    )
    multiplot_tab.model.add_plot(plot_tab, "Label 1", color="#ff0000")
    return multiplot_tab


class TestSheets:
    def test_simple_project_without_plot_with_plot(
        self, simple_project: MainWindow
    ) -> None:
        tabs = [
            simple_project.ui.tabWidget.widget(idx)
            for idx in range(simple_project.ui.tabWidget.count())
        ]

        assert len(tabs) == 3
        assert isinstance(tabs[0], DataSheet)
        assert isinstance(tabs[1], DataSheet)
        assert isinstance(tabs[2], PlotTab)

    @pytest.mark.skip("shows GUI")
    def test_show_simple_project(self, project_with_multiplot: MainWindow) -> None:
        qapp = QtWidgets.QApplication.instance()
        project_with_multiplot.show()
        qapp.exec()

    def test_close_sheet_without_any_plots(
        self, simple_project_without_plot: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(simple_project_without_plot, "confirm_close_dialog")

        simple_project_without_plot.confirm_close_dialog.return_value = False
        assert simple_project_without_plot.ui.tabWidget.count() == 2
        simple_project_without_plot.close_tab_with_children(1)
        assert simple_project_without_plot.ui.tabWidget.count() == 2

        simple_project_without_plot.confirm_close_dialog.return_value = True
        simple_project_without_plot.close_tab_with_children(1)
        assert simple_project_without_plot.ui.tabWidget.count() == 1
        sheet: DataSheet = simple_project_without_plot.ui.tabWidget.widget(0)
        assert sheet.name == "Sheet 1"

    def test_close_unused_plot(
        self, simple_project: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(simple_project, "confirm_close_dialog")

        # check that tab under test is indeed a plot
        PLOT_IDX = 2
        assert isinstance(simple_project.ui.tabWidget.widget(PLOT_IDX), PlotTab)

        # cancel close request
        simple_project.confirm_close_dialog.return_value = False
        assert simple_project.ui.tabWidget.count() == 3
        simple_project.close_tab_with_children(PLOT_IDX)
        assert simple_project.ui.tabWidget.count() == 3

        # confirm close request
        simple_project.confirm_close_dialog.return_value = True
        simple_project.close_tab_with_children(PLOT_IDX)
        assert simple_project.ui.tabWidget.count() == 2
        for idx in range(2):
            widget = simple_project.ui.tabWidget.widget(idx)
            assert isinstance(widget, DataSheet)

    def test_close_multiplot(
        self, project_with_multiplot: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(project_with_multiplot, "confirm_close_dialog")
        project_with_multiplot.confirm_close_dialog.return_value = True

        # A multiplot in tab 3
        project_with_multiplot.close_tab_with_children(3)

        # Only the two sheets and the plot remain, the multiplot is gone
        assert project_with_multiplot.ui.tabWidget.count() == 3
        assert project_with_multiplot.ui.tabWidget.widget(0).name == "Sheet 1"
        assert project_with_multiplot.ui.tabWidget.widget(1).name == "Sheet 2"
        assert project_with_multiplot.ui.tabWidget.widget(2).name == "Plot 1"

    def test_close_plot_with_associated_multiplots(
        self, project_with_multiplot: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(project_with_multiplot, "confirm_close_dialog")
        project_with_multiplot.confirm_close_dialog.return_value = True

        # A plot in tab 2 with an associated multiplot in tab 3
        project_with_multiplot.close_tab_with_children(2)

        # Only the two sheets remain, the plot and multiplot are gone
        assert project_with_multiplot.ui.tabWidget.count() == 2
        assert project_with_multiplot.ui.tabWidget.widget(0).name == "Sheet 1"
        assert project_with_multiplot.ui.tabWidget.widget(1).name == "Sheet 2"

    def test_close_plot_lists_associated_multiplots(
        self, project_with_multiplot: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(project_with_multiplot, "confirm_close_dialog")
        project_with_multiplot.confirm_close_dialog.return_value = False

        # A plot in tab 2 with an associated multiplot in tab 3
        project_with_multiplot.close_tab_with_children(2)

        assert (
            "Multiplot 1"
            in project_with_multiplot.confirm_close_dialog.call_args.args[0]
        )

    def test_close_sheet_with_no_plots(
        self, simple_project: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(simple_project, "confirm_close_dialog")
        simple_project.confirm_close_dialog.return_value = True

        simple_project.close_tab_with_children(0)

        assert simple_project.ui.tabWidget.count() == 2
        assert simple_project.ui.tabWidget.widget(0).name == "Sheet 2"

    def test_close_sheet_with_associated_plots(
        self, project_with_multiplot: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(project_with_multiplot, "confirm_close_dialog")
        project_with_multiplot.confirm_close_dialog.return_value = True

        # tab 1 (Sheet2) has one associated plot in tab 2 and a multiplot
        project_with_multiplot.close_tab_with_children(1)

        assert project_with_multiplot.ui.tabWidget.count() == 1
        assert project_with_multiplot.ui.tabWidget.widget(0).name == "Sheet 1"

    def test_close_sheet_lists_associated_plots(
        self, project_with_multiplot: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(project_with_multiplot, "confirm_close_dialog")
        project_with_multiplot.confirm_close_dialog.return_value = False

        # no associated plots
        project_with_multiplot.close_tab_with_children(0)
        assert (
            "Plot 1"
            not in project_with_multiplot.confirm_close_dialog.call_args.args[0]
        )
        assert (
            "Multiplot 1"
            not in project_with_multiplot.confirm_close_dialog.call_args.args[0]
        )

        # associated plots: Plot 1, Multiplot 1
        project_with_multiplot.close_tab_with_children(1)
        assert "Plot 1" in project_with_multiplot.confirm_close_dialog.call_args.args[0]
        assert (
            "Multiplot 1"
            in project_with_multiplot.confirm_close_dialog.call_args.args[0]
        )

    def test_close_last_remaining_tabs_starts_new_project(
        self, simple_project: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(simple_project, "confirm_close_dialog")
        mocker.patch.object(simple_project, "clear_all")
        simple_project.confirm_close_dialog.return_value = True

        # close Sheet1
        simple_project.close_tab_with_children(0)
        # close Sheet2; should also close Plot1 and start new project
        simple_project.close_tab_with_children(0)

        simple_project.clear_all.assert_called_with(add_sheet=True)

    def test_remove_unused_column(
        self, simple_project: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(dialogs, "show_warning_dialog")
        simple_project.ui.tabWidget.setCurrentIndex(1)
        sheet: DataSheet = simple_project.ui.tabWidget.currentWidget()
        mocker.patch.object(sheet, "remove_selected_columns")

        # no associated plots or columns, confirmation not needed
        sheet.ui.data_view.selectColumn(4)
        simple_project.remove_selected_columns()
        dialogs.show_warning_dialog.assert_not_called()
        sheet.remove_selected_columns.assert_called()

    def test_remove_used_column_lists_associated_plots(
        self, simple_project: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(dialogs, "show_warning_dialog")
        simple_project.ui.tabWidget.setCurrentIndex(1)
        sheet: DataSheet = simple_project.ui.tabWidget.currentWidget()
        mocker.patch.object(sheet, "remove_selected_columns")

        # associated plots: Plot 1
        sheet.ui.data_view.selectColumn(0)
        simple_project.remove_selected_columns()
        dialogs.show_warning_dialog.assert_called()
        assert "Plot 1" in dialogs.show_warning_dialog.call_args.kwargs["msg"]
        sheet.remove_selected_columns.assert_not_called()

    def test_remove_used_column_lists_associated_calculated_columns(
        self, simple_project: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(dialogs, "show_warning_dialog")
        simple_project.ui.tabWidget.setCurrentIndex(1)
        sheet: DataSheet = simple_project.ui.tabWidget.currentWidget()
        mocker.patch.object(sheet, "remove_selected_columns")

        # associated plots: Plot 1
        sheet.ui.data_view.selectColumn(0)
        simple_project.remove_selected_columns()
        dialogs.show_warning_dialog.assert_called()
        assert "'z', 'position'" in dialogs.show_warning_dialog.call_args.kwargs["msg"]
        assert "empty" not in dialogs.show_warning_dialog.call_args.kwargs["msg"]
        assert "yerr" not in dialogs.show_warning_dialog.call_args.kwargs["msg"]
        sheet.remove_selected_columns.assert_not_called()

    def test_remove_column_and_used_column(
        self, simple_project: MainWindow, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(dialogs, "show_warning_dialog")
        simple_project.ui.tabWidget.setCurrentIndex(1)
        sheet: DataSheet = simple_project.ui.tabWidget.currentWidget()
        mocker.patch.object(sheet, "remove_selected_columns")

        # column 'position' is only used by 'use_pos', delete both
        sheet.ui.data_view.selectColumn(5)
        sheet.selection.select(
            sheet.model.index(0, 6),
            QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Columns,
        )
        simple_project.remove_selected_columns()

        dialogs.show_warning_dialog.assert_not_called()
        sheet.remove_selected_columns.assert_called()

    def test_duplicate_sheet(self, simple_project: MainWindow) -> None:
        simple_project.ui.tabWidget.setCurrentIndex(1)
        sheet1: DataSheet = simple_project.ui.tabWidget.currentWidget()

        simple_project.duplicate_data_sheet()

        assert simple_project.ui.tabWidget.count() == 4
        sheet2: DataSheet = simple_project.ui.tabWidget.widget(3)
        assert (
            sheet1.model.data_model.get_column("col1").tolist()
            == sheet2.model.data_model.get_column("col1").tolist()
        )

    def test_duplicate_sheet_with_plots(self, simple_project: MainWindow) -> None:
        simple_project.ui.tabWidget.setCurrentIndex(1)
        sheet1: DataSheet = simple_project.ui.tabWidget.widget(1)
        plot1: PlotTab = simple_project.ui.tabWidget.widget(2)

        simple_project.duplicate_data_sheet_with_plots()

        assert simple_project.ui.tabWidget.count() == 5
        sheet2: DataSheet = simple_project.ui.tabWidget.widget(3)
        plot2: PlotTab = simple_project.ui.tabWidget.widget(4)
        assert (
            sheet1.model.data_model.get_column("col1").tolist()
            == sheet2.model.data_model.get_column("col1").tolist()
        )
        # check that plot2 points to the new data sheet
        assert plot1.data_sheet == sheet1
        assert plot2.data_sheet == sheet2
        # check that the underlying plot models are not identical
        assert plot1.model != plot2.model
        # check a few model attributes, they should have identical values
        assert plot1.model._parameters["a"].value == plot2.model._parameters["a"].value
        assert plot1.model.get_model_expression() == plot2.model.get_model_expression()

    def test_duplicate_plot(self, simple_project: MainWindow) -> None:
        simple_project.ui.tabWidget.setCurrentIndex(2)

        simple_project.duplicate_plot()

        assert simple_project.ui.tabWidget.count() == 4
        assert simple_project._plot_num == 2
        plot1: PlotTab = simple_project.ui.tabWidget.widget(2)
        plot2: PlotTab = simple_project.ui.tabWidget.widget(3)
        assert plot1.name == "Plot 1"
        assert plot2.name == "Plot 2"
        # check that underlying data sheets are identical
        assert plot1.data_sheet is plot2.data_sheet
        # check that the underlying plot models are not identical
        assert plot1.model != plot2.model
        # check that plot ids are not identical
        assert plot1.id != plot2.id
        assert plot1.model._parameters["a"].value == plot2.model._parameters["a"].value
        assert plot1.model.get_model_expression() == plot2.model.get_model_expression()

    def test_get_data_sheets(self, simple_project: MainWindow) -> None:
        tabwidget = simple_project.ui.tabWidget
        sheet1 = tabwidget.widget(0)
        sheet2 = tabwidget.widget(1)
        assert type(sheet1) is type(sheet2) is DataSheet

        sheets = simple_project.get_data_sheets()

        assert sheets == [sheet1, sheet2]

    def test_change_plot_source(self, project_with_two_sheets: MainWindow) -> None:
        plot: PlotTab = project_with_two_sheets.ui.tabWidget.widget(2)
        sheet3: DataSheet = project_with_two_sheets.ui.tabWidget.widget(3)

        plot.change_data_source(
            sheet3,
            x_col_name="t",
            y_col_name="pos",
            x_err_col_name="err_t",
            y_err_col_name="err_pos",
        )

        assert plot.data_sheet == sheet3
        assert plot.model.data_model == sheet3.model.data_model
        assert sheet3.model.data_model.get_column_name(plot.model.x_col) == "t"
        assert sheet3.model.data_model.get_column_name(plot.model.x_err_col) == "err_t"
        assert sheet3.model.data_model.get_column_name(plot.model.y_col) == "pos"
        assert (
            sheet3.model.data_model.get_column_name(plot.model.y_err_col) == "err_pos"
        )
        assert plot.model.get_model_expression() == "a * x + b"

    def test_import_csv_asks_confirmation_if_dirty(
        self,
        simple_project: MainWindow,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(simple_project, "confirm_project_close_dialog")
        mocker.patch.object(simple_project, "get_open_filename_dialog")
        simple_project.confirm_project_close_dialog.return_value = False
        # select sheet 2 with actual data
        simple_project.ui.tabWidget.setCurrentIndex(1)
        simple_project.mark_project_dirty()

        simple_project.import_csv()

        simple_project.confirm_project_close_dialog.assert_called()
        not simple_project.get_open_filename_dialog.assert_not_called()

    def test_import_csv_doesnt_ask_confirmation_on_empty_sheet(
        self,
        simple_project: MainWindow,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(simple_project, "confirm_project_close_dialog")
        mocker.patch.object(simple_project, "get_open_filename_dialog")
        simple_project.get_open_filename_dialog.return_value = None
        # add new empty sheet
        simple_project.add_data_sheet()

        simple_project.import_csv()

        simple_project.confirm_project_close_dialog.assert_not_called()
        simple_project.get_open_filename_dialog.assert_called()
