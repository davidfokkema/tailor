from unittest.mock import sentinel

import numpy as np
import pyqtgraph
import pytest
from PySide6 import QtCore
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
        mocker.patch.object(plot_tab, "update_model_widget")
        mocker.patch.object(plot_tab, "update_info_box")
        mocker.patch.object(plot_tab, "update_plot")

        plot_tab.update_ui()

        plot_tab.update_model_widget.assert_called()
        plot_tab.update_plot.assert_called()
        plot_tab.update_info_box.assert_called()

    def test_update_function_label(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab.model, "get_y_col_name")
        plot_tab.model.get_y_col_name.return_value = "foo"

        plot_tab.update_model_widget()

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
        plot_tab.model.best_fit = None
        plot_tab.update_info_box()

    def test_update_xlabel_sets_model_attr(self, plot_tab: PlotTab):
        plot_tab.update_xlabel()

        assert plot_tab.model.x_label == plot_tab.ui.xlabel.text.return_value

    def test_update_ylabel_sets_model_attr(self, plot_tab: PlotTab):
        plot_tab.update_ylabel()

        assert plot_tab.model.y_label == plot_tab.ui.ylabel.text.return_value

    @pytest.mark.parametrize("textvalue, value", [("4.4", 4.4), ("", None)])
    def test_update_x_min_sets_model_attr(
        self, plot_tab: PlotTab, mocker: MockerFixture, textvalue, value
    ):
        mocker.patch.object(plot_tab, "update_limits")
        plot_tab.ui.x_min.text.return_value = textvalue

        plot_tab.update_x_min()

        assert plot_tab.model.x_min == value
        plot_tab.update_limits.assert_called()

    @pytest.mark.parametrize("textvalue, value", [("4.4", 4.4), ("", None)])
    def test_update_x_max_sets_model_attr(
        self, plot_tab: PlotTab, mocker: MockerFixture, textvalue, value
    ):
        mocker.patch.object(plot_tab, "update_limits")
        plot_tab.ui.x_max.text.return_value = textvalue

        plot_tab.update_x_max()

        assert plot_tab.model.x_max == value
        plot_tab.update_limits.assert_called()

    @pytest.mark.parametrize("textvalue, value", [("4.4", 4.4), ("", None)])
    def test_update_y_min_sets_model_attr(
        self, plot_tab: PlotTab, mocker: MockerFixture, textvalue, value
    ):
        mocker.patch.object(plot_tab, "update_limits")
        plot_tab.ui.y_min.text.return_value = textvalue

        plot_tab.update_y_min()

        assert plot_tab.model.y_min == value
        plot_tab.update_limits.assert_called()

    @pytest.mark.parametrize("textvalue, value", [("4.4", 4.4), ("", None)])
    def test_update_y_max_sets_model_attr(
        self, plot_tab: PlotTab, mocker: MockerFixture, textvalue, value
    ):
        mocker.patch.object(plot_tab, "update_limits")
        plot_tab.ui.y_max.text.return_value = textvalue

        plot_tab.update_y_max()

        assert plot_tab.model.y_max == value
        plot_tab.update_limits.assert_called()

    @pytest.mark.parametrize(
        "x_min, x_max, y_min, y_max, expected",
        [
            (None, None, None, None, (1.0, 2.0, 3.0, 4.0)),
            (1.5, 2.5, 3.5, 4.5, (1.5, 2.5, 3.5, 4.5)),
        ],
    )
    def test_get_adjusted_limits(
        self, plot_tab: PlotTab, x_min, x_max, y_min, y_max, expected
    ):
        plot_tab.model.get_limits_from_data.return_value = (1.0, 2.0, 3.0, 4.0)
        plot_tab.model.x_min = x_min
        plot_tab.model.x_max = x_max
        plot_tab.model.y_min = y_min
        plot_tab.model.y_max = y_max

        actual = plot_tab.get_adjusted_limits()

        assert actual == expected

    def test_use_fit_domain(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab, "get_fit_curve_x_limits")
        plot_tab.get_fit_curve_x_limits.return_value = -1, 1
        plot_tab.model.best_fit = sentinel.fit
        state = QtCore.Qt.Checked.value

        plot_tab.toggle_use_fit_domain(state)

        plot_tab.ui.plot_widget.addItem.assert_called_with(plot_tab.fit_domain_area)
        assert plot_tab.model.use_fit_domain is True
        assert plot_tab.model.best_fit is None

    def test_dont_use_fit_domain(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab, "get_fit_curve_x_limits")
        plot_tab.get_fit_curve_x_limits.return_value = -1, 1
        plot_tab.model.best_fit = sentinel.fit
        state = QtCore.Qt.Unchecked.value

        plot_tab.toggle_use_fit_domain(state)

        plot_tab.ui.plot_widget.removeItem.assert_called_with(plot_tab.fit_domain_area)
        assert plot_tab.model.use_fit_domain is False
        assert plot_tab.model.best_fit is None

    def test_fit_domain_region_changed(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab, "fit_domain_area")
        mocker.patch.object(plot_tab, "plot_best_fit")
        plot_tab.fit_domain_area.getRegion.return_value = sentinel.x_min, sentinel.x_max
        plot_tab.model.best_fit = sentinel.fit
        plot_tab.model.use_fit_domain = True

        plot_tab.fit_domain_region_changed()

        plot_tab.ui.fit_start_box.setValue.assert_called_with(sentinel.x_min)
        plot_tab.ui.fit_end_box.setValue.assert_called_with(sentinel.x_max)
        assert plot_tab.model.best_fit is None
        plot_tab.plot_best_fit.assert_called()

    def test_fit_domain_region_changed_without_use(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        mocker.patch.object(plot_tab, "plot_best_fit")
        plot_tab.model.best_fit = sentinel.fit
        plot_tab.model.use_fit_domain = False

        plot_tab.fit_domain_region_changed()

        plot_tab.plot_best_fit.assert_not_called()
        assert plot_tab.model.best_fit == sentinel.fit

    def test_update_fit_domain_sets_model_attribute(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        mocker.patch.object(plot_tab, "fit_domain_area")
        plot_tab.ui.fit_start_box.value.return_value = -10.0
        plot_tab.ui.fit_end_box.value.return_value = 5.0

        plot_tab.update_fit_domain()

        plot_tab.fit_domain_area.setRegion.assert_called_with((-10.0, 5.0))
        assert plot_tab.model.fit_domain == (-10.0, 5.0)

    def test_update_fit_domain_with_invalid_domain(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        mocker.patch.object(plot_tab, "fit_domain_area")
        plot_tab.model.fit_domain = sentinel.domain
        plot_tab.ui.fit_start_box.value.return_value = 5.0
        plot_tab.ui.fit_end_box.value.return_value = -10

        plot_tab.update_fit_domain()

        # nothing should have been updated
        plot_tab.fit_domain_area.setRegion.assert_not_called()
        assert plot_tab.model.fit_domain == sentinel.domain

    def test_get_fit_curve_x_limits_on_data(self, plot_tab: PlotTab):
        plot_tab.ui.draw_curve_option.currentIndex.return_value = (
            tailor.plot_tab.DRAW_CURVE_ON_DATA
        )
        plot_tab.model.get_limits_from_data.return_value = (
            sentinel.x_min,
            sentinel.x_max,
            None,
            None,
        )

        assert plot_tab.get_fit_curve_x_limits() == (sentinel.x_min, sentinel.x_max)

    def test_get_fit_curve_x_limits_on_domain(self, plot_tab: PlotTab):
        plot_tab.ui.draw_curve_option.currentIndex.return_value = (
            tailor.plot_tab.DRAW_CURVE_ON_DOMAIN
        )
        plot_tab.model.fit_domain = (sentinel.x_min, sentinel.x_max)

        assert plot_tab.get_fit_curve_x_limits() == (sentinel.x_min, sentinel.x_max)

    def test_get_fit_curve_x_limits_on_axis(self, plot_tab: PlotTab):
        plot_tab.ui.draw_curve_option.currentIndex.return_value = (
            tailor.plot_tab.DRAW_CURVE_ON_AXIS
        )
        plot_tab.ui.plot_widget.viewRange.return_value = [
            [sentinel.x_min, sentinel.x_max],
            [None, None],
        ]

        assert plot_tab.get_fit_curve_x_limits() == (sentinel.x_min, sentinel.x_max)

    def test_get_fit_curve_x_limits_not_implemented(self, plot_tab: PlotTab):
        plot_tab.ui.draw_curve_option.currentIndex.return_value = 10

        with pytest.raises(NotImplementedError):
            plot_tab.get_fit_curve_x_limits()
