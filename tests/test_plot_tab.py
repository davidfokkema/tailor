from unittest.mock import sentinel

import pyqtgraph
import pytest
from pytest_mock import MockerFixture

import tailor.plot_tab
from tailor.data_sheet import DataSheet
from tailor.plot_tab import PlotTab


@pytest.fixture()
def plot_tab(mocker: MockerFixture):
    mocker.patch.object(tailor.plot_tab, "Ui_PlotTab")
    mocker.patch.object(tailor.plot_tab, "PlotModel")
    mocker.patch.object(PlotTab, "finish_ui")
    data_sheet = mocker.Mock(spec=DataSheet)
    return PlotTab(
        data_sheet,
        sentinel.x_col,
        sentinel.y_col,
        sentinel.x_err_col,
        sentinel.y_err_col,
    )


class TestImplementationDetails:
    def test_init(self, mocker: MockerFixture):
        PlotModel_ = mocker.patch.object(tailor.plot_tab, "PlotModel")
        mocker.patch.object(PlotTab, "create_plot")
        mocker.patch.object(PlotTab, "finish_ui")
        mocker.patch.object(PlotTab, "connect_ui_events")
        mock_data_sheet = mocker.Mock(spec=DataSheet)
        mock_data_sheet.data_model._data = sentinel.data_model

        plot_tab = PlotTab(
            mock_data_sheet,
            sentinel.x_col,
            sentinel.y_col,
            sentinel.x_err_col,
            sentinel.y_err_col,
        )

        assert plot_tab.model == PlotModel_.return_value
        PlotModel_.assert_called_with(
            sentinel.data_model,
            sentinel.x_col,
            sentinel.y_col,
            sentinel.x_err_col,
            sentinel.y_err_col,
        )
        assert isinstance(plot_tab.data_sheet, DataSheet) is True
        plot_tab.create_plot.assert_called()
        plot_tab.finish_ui.assert_called()
        plot_tab.connect_ui_events.assert_called()


class TestPlotTab:
    def test_create_plot(self, plot_tab: PlotTab, mocker: MockerFixture):
        pg: pyqtgraph = mocker.patch.object(tailor.plot_tab, "pg")

        plot_tab.create_plot()

        assert plot_tab.plot == plot_tab.ui.plot_widget.plot.return_value
        pg.ErrorBarItem.assert_called()
        assert plot_tab.initial_param_plot == plot_tab.ui.plot_widget.plot.return_value
        assert plot_tab.fit_plot == plot_tab.ui.plot_widget.plot.return_value
        assert plot_tab.fit_domain_area == pg.LinearRegionItem.return_value
