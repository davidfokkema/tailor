from unittest.mock import sentinel

import numpy as np
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

    def test_update_ui(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab, "update_function_label")
        mocker.patch.object(plot_tab, "update_info_box")
        mocker.patch.object(plot_tab, "update_plot")

        plot_tab.update_ui()

        plot_tab.update_function_label.assert_called()
        plot_tab.update_plot.assert_called()
        plot_tab.update_info_box.assert_called()

    def test_update_function_label(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab.model, "get_y_col_name")
        plot_tab.model.get_y_col_name.return_value = "foo"

        plot_tab.update_function_label()

        plot_tab.model.get_y_col_name.assert_called()
        plot_tab.ui.model_func_label.setText.assert_called_with("Function: foo =")

    def test_update_plot_with_errors(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab, "error_bars")
        mocker.patch.object(plot_tab, "update_limits")
        x = np.array([0, 1, 2])
        y = np.array([0, 1, 4])
        xerr = np.array([0.5, 0.7, 0.4])
        yerr = np.array([0.4, 0.5, 0.3])
        plot_tab.model.get_data.return_value = (x, y, xerr, yerr)

        plot_tab.update_plot()

        plot_tab.plot.setData.assert_called_with(x, y)
        kwargs = plot_tab.error_bars.setData.call_args.kwargs
        assert kwargs["x"] == pytest.approx(x)
        assert kwargs["y"] == pytest.approx(y)
        assert kwargs["width"] == pytest.approx([1, 1.4, 0.8])
        assert kwargs["height"] == pytest.approx([0.8, 1.0, 0.6])
        plot_tab.update_limits.assert_called()

    def test_info_box(self, plot_tab: PlotTab):
        plot_tab.model.fit = None

        plot_tab.update_info_box()

    def test_get_adjusted_limits(self, plot_tab: PlotTab, mocker: MockerFixture):
        # minimal testing, otherwise we're just copying the implementation
        mocker.patch.object(plot_tab, "update_value_from_text")
        plot_tab.model.get_limits_from_data.return_value = 0.0, 10.0, 20.0, 30.0

        actual = plot_tab.get_adjusted_limits()

        assert len(actual) == 4
        plot_tab.model.get_limits_from_data.assert_called()
        assert plot_tab.update_value_from_text.call_count == 4

    def test_update_value_from_text(self, plot_tab: PlotTab, mocker: MockerFixture):
        widget = mocker.Mock()

        widget.text.return_value = ""
        assert plot_tab.update_value_from_text(4.0, widget) == 4.0
        widget.text.return_value = "5.5"
        assert plot_tab.update_value_from_text(4.0, widget) == 5.5
