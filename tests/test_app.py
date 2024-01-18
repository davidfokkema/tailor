import numpy as np
import pytest
from PySide6 import QtWidgets
from pytest_mock import MockerFixture

from tailor.app import Application
from tailor.data_sheet import DataSheet
from tailor.plot_tab import DRAW_CURVE_OPTIONS, DrawCurve, PlotTab


@pytest.fixture()
def data_sheet(mocker: MockerFixture) -> DataSheet:
    sheet = DataSheet(name="Sheet2", id=1234, main_window=mocker.MagicMock())
    sheet.data_model.setDataFromArray(
        sheet.data_model.createIndex(0, 0),
        np.array(
            [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [float("nan"), 1.0, 4.0, 9.0, 16.0, 25.0]]
        ).T,
    )
    sheet.data_model.insertCalculatedColumn(2)
    sheet.data_model.insertCalculatedColumn(3)
    sheet.data_model.insertCalculatedColumn(4)
    sheet.data_model.renameColumn(0, "x")
    sheet.data_model.renameColumn(1, "y")
    sheet.data_model.renameColumn(2, "z")
    sheet.data_model.renameColumn(3, "yerr")
    sheet.data_model.renameColumn(4, "empty")
    sheet.data_model.updateColumnExpression(2, "0.02 * x ** 2")
    sheet.data_model.updateColumnExpression(3, "0.1")
    return sheet


@pytest.fixture()
def plot_tab(data_sheet: DataSheet, mocker: MockerFixture) -> PlotTab:
    plot_tab = PlotTab(
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
def simple_project_without_plot(data_sheet: DataSheet) -> Application:
    app = Application(add_sheet=True)
    app.ui.tabWidget.addTab(data_sheet, data_sheet.name)
    return app


@pytest.fixture()
def simple_project(
    simple_project_without_plot: Application, plot_tab: PlotTab
) -> Application:
    simple_project_without_plot.ui.tabWidget.addTab(plot_tab, plot_tab.name)
    return simple_project_without_plot


class TestSheets:
    def test_simple_project_without_plot_with_plot(
        self, simple_project: Application
    ) -> None:
        tabs = [
            simple_project.ui.tabWidget.widget(idx)
            for idx in range(simple_project.ui.tabWidget.count())
        ]

        assert len(tabs) == 3
        assert isinstance(tabs[0], DataSheet)
        assert isinstance(tabs[1], DataSheet)
        assert isinstance(tabs[2], PlotTab)

        # qapp = QtWidgets.QApplication.instance()
        # simple_project.show()
        # qapp.exec()

    def test_close_sheet_without_plots(
        self, simple_project_without_plot: Application
    ) -> None:
        ...
