from unittest.mock import sentinel

import numpy as np
import pyqtgraph
import pytest
from PySide6 import QtCore
from pytest_mock import MockerFixture

import tailor.plot_tab
from tailor.data_sheet import DataSheet
from tailor.plot_model import PlotModel
from tailor.plot_tab import DRAW_CURVE_OPTIONS, DrawCurve, PlotTab


@pytest.fixture()
def plot_tab(mocker: MockerFixture):
    mocker.patch.object(tailor.plot_tab, "Ui_PlotTab")
    mocker.patch.object(tailor.plot_tab, "PlotModel", spec=PlotModel)
    mocker.patch.object(PlotTab, "set_fit_domain_from_data")
    mocker.patch.object(PlotTab, "finish_ui")
    data_sheet = mocker.Mock(spec=DataSheet)
    return PlotTab(
        main_window=mocker.Mock(),
        name="Plot 1",
        id=12345,
        data_sheet=data_sheet,
        x_col=sentinel.x_col,
        y_col=sentinel.y_col,
        x_err_col=sentinel.x_err_col,
        y_err_col=sentinel.y_err_col,
    )


class TestImplementationDetails:
    def test_init(self, mocker: MockerFixture):
        PlotModel_ = mocker.patch.object(tailor.plot_tab, "PlotModel")
        mocker.patch.object(PlotTab, "set_fit_domain_from_data")
        mocker.patch.object(PlotTab, "create_plot")
        mocker.patch.object(PlotTab, "finish_ui")
        mocker.patch.object(PlotTab, "connect_ui_events")
        mock_data_sheet = mocker.Mock(spec=DataSheet)
        mock_data_sheet.model.data_model = sentinel.data_model

        plot_tab = PlotTab(
            main_window=mocker.Mock(),
            name=sentinel.name,
            id=sentinel.id,
            data_sheet=mock_data_sheet,
            x_col=sentinel.x_col,
            y_col=sentinel.y_col,
            x_err_col=sentinel.x_err_col,
            y_err_col=sentinel.y_err_col,
        )

        assert plot_tab.name == sentinel.name
        assert plot_tab.model == PlotModel_.return_value
        PlotModel_.assert_called_with(
            sentinel.data_model,
            sentinel.x_col,
            sentinel.y_col,
            sentinel.x_err_col,
            sentinel.y_err_col,
        )
        assert isinstance(plot_tab.data_sheet, DataSheet) is True
        plot_tab.set_fit_domain_from_data.assert_called()
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

    def test_refresh_ui(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab, "update_model_widget")
        mocker.patch.object(plot_tab, "update_plot")
        mocker.patch.object(plot_tab, "update_params_ui_values_from_model")
        mocker.patch.object(plot_tab, "update_model_curves")
        mocker.patch.object(plot_tab, "update_info_box")
        mocker.patch.object(plot_tab, "update_fit_domain_from_model")

        plot_tab.refresh_ui()

        plot_tab.update_model_widget.assert_called()
        plot_tab.update_plot.assert_called()
        plot_tab.model.verify_best_fit_data.assert_called()
        plot_tab.update_params_ui_values_from_model()
        plot_tab.update_model_curves.assert_called()
        plot_tab.update_info_box.assert_called()
        plot_tab.update_fit_domain_from_model.assert_called()

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
            (0, 0, 0, 0, (0, 0, 0, 0)),
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
        mocker.patch.object(plot_tab, "update_model_curves")
        state = QtCore.Qt.Checked.value

        plot_tab.set_use_fit_domain(state)

        plot_tab.ui.plot_widget.addItem.assert_called_with(plot_tab.fit_domain_area)
        plot_tab.model.set_fit_domain_enabled.assert_called_with(True)
        plot_tab.update_model_curves.assert_called()

    def test_dont_use_fit_domain(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab, "update_model_curves")
        state = QtCore.Qt.Unchecked.value

        plot_tab.set_use_fit_domain(state)

        plot_tab.ui.plot_widget.removeItem.assert_called_with(plot_tab.fit_domain_area)
        plot_tab.model.set_fit_domain_enabled.assert_called_with(False)
        plot_tab.update_model_curves.assert_called()

    def test_fit_domain_region_changed(self, plot_tab: PlotTab, mocker: MockerFixture):
        mocker.patch.object(plot_tab, "fit_domain_area")
        plot_tab.fit_domain_area.getRegion.return_value = sentinel.x_min, sentinel.x_max
        plot_tab.model.best_fit = sentinel.fit

        plot_tab.fit_domain_region_changed()

        plot_tab.ui.fit_start_box.setValue.assert_called_with(sentinel.x_min)
        plot_tab.ui.fit_end_box.setValue.assert_called_with(sentinel.x_max)

    @pytest.mark.parametrize(
        "new_xmin, old_xmax, domain",
        [(1.0, 3.0, (1.0, 3.0)), (4.0, 3.0, (4.0, 4.0)), (1.0, -1.0, (1.0, 1.0))],
    )
    def test_update_fit_domain_xmin(
        self, plot_tab: PlotTab, mocker: MockerFixture, new_xmin, old_xmax, domain
    ):
        mocker.patch.object(plot_tab, "fit_domain_area")
        mocker.patch.object(plot_tab, "update_model_curves")
        plot_tab.ui.fit_end_box.value.return_value = old_xmax

        plot_tab.update_fit_domain_xmin(mocker.Mock(), new_xmin)

        xmin, xmax = domain
        plot_tab.fit_domain_area.setRegion.assert_called_with((xmin, xmax))
        plot_tab.model.set_fit_domain.assert_called_with(xmin=xmin, xmax=xmax)
        if xmax != old_xmax:
            plot_tab.ui.fit_end_box.setValue.assert_called_with(xmax)
        else:
            plot_tab.ui.fit_end_box.setValue.assert_not_called()
        plot_tab.update_model_curves.assert_called()

    @pytest.mark.parametrize(
        "old_xmin, new_xmax, domain",
        [(1.0, 3.0, (1.0, 3.0)), (4.0, 3.0, (3.0, 3.0)), (1.0, -1.0, (-1.0, -1.0))],
    )
    def test_update_fit_domain_xmax(
        self, plot_tab: PlotTab, mocker: MockerFixture, old_xmin, new_xmax, domain
    ):
        mocker.patch.object(plot_tab, "fit_domain_area")
        mocker.patch.object(plot_tab, "update_model_curves")
        plot_tab.ui.fit_start_box.value.return_value = old_xmin

        plot_tab.update_fit_domain_xmax(mocker.Mock(), new_xmax)

        xmin, xmax = domain
        plot_tab.fit_domain_area.setRegion.assert_called_with((xmin, xmax))
        plot_tab.model.set_fit_domain.assert_called_with(xmin=xmin, xmax=xmax)
        if xmin != old_xmin:
            plot_tab.ui.fit_start_box.setValue.assert_called_with(xmin)
        else:
            plot_tab.ui.fit_start_box.setValue.assert_not_called()
        plot_tab.update_model_curves.assert_called()

    def test_get_fit_curve_x_limits_on_data(self, plot_tab: PlotTab):
        plot_tab.ui.draw_curve_option.currentIndex.return_value = list(
            DRAW_CURVE_OPTIONS.keys()
        ).index(tailor.plot_tab.DrawCurve.ON_DATA)
        plot_tab.model.get_limits_from_data.return_value = (
            sentinel.x_min,
            sentinel.x_max,
            None,
            None,
        )

        assert plot_tab.get_fit_curve_x_limits() == (sentinel.x_min, sentinel.x_max)

    def test_get_fit_curve_x_limits_on_domain(self, plot_tab: PlotTab):
        plot_tab.ui.draw_curve_option.currentIndex.return_value = list(
            DRAW_CURVE_OPTIONS.keys()
        ).index(tailor.plot_tab.DrawCurve.ON_DOMAIN)
        plot_tab.model.get_fit_domain.return_value = (sentinel.x_min, sentinel.x_max)

        assert plot_tab.get_fit_curve_x_limits() == (sentinel.x_min, sentinel.x_max)

    def test_get_fit_curve_x_limits_on_axis(self, plot_tab: PlotTab):
        plot_tab.ui.draw_curve_option.currentIndex.return_value = list(
            DRAW_CURVE_OPTIONS.keys()
        ).index(tailor.plot_tab.DrawCurve.ON_AXIS)
        plot_tab.ui.plot_widget.viewRange.return_value = [
            [sentinel.x_min, sentinel.x_max],
            [None, None],
        ]

        assert plot_tab.get_fit_curve_x_limits() == (sentinel.x_min, sentinel.x_max)

    def test_update_parameter_value_updates_parameter(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        mocker.patch.object(plot_tab, "update_model_curves")
        widget = mocker.Mock(_parameter="param")

        plot_tab.update_parameter_value(widget, 14.7)

        plot_tab.model.set_parameter_value.assert_called_with("param", 14.7)
        plot_tab.update_model_curves.assert_called()

    def test_update_parameter_min_bound_updates_parameter(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        mocker.patch.object(plot_tab, "update_model_curves")
        widget = mocker.Mock(_parameter="param")

        plot_tab.update_parameter_min_bound(widget, 14.7)

        plot_tab.model.set_parameter_min_value.assert_called_with("param", 14.7)
        plot_tab.update_model_curves.assert_called()

    def test_update_parameter_max_bound_updates_parameter(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        mocker.patch.object(plot_tab, "update_model_curves")
        widget = mocker.Mock(_parameter="param")

        plot_tab.update_parameter_max_bound(widget, 14.7)

        plot_tab.model.set_parameter_max_value.assert_called_with("param", 14.7)
        plot_tab.update_model_curves.assert_called()

    def test_update_parameter_fixed_state_updates_parameter(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        mocker.patch.object(plot_tab, "update_model_curves")
        widget = mocker.Mock(_parameter="param")

        plot_tab.update_parameter_fixed_state(widget, True)

        plot_tab.model.set_parameter_vary_state.assert_called_with("param", False)
        plot_tab.update_model_curves.assert_called()

    def test_update_params_ui(self, plot_tab: PlotTab, mocker: MockerFixture):
        plot_tab._params = {"a": mocker.Mock(), "b": mocker.Mock(), "e": mocker.Mock()}
        plot_tab.model.get_parameter_names.return_value = ["b", "c", "d"]
        mocker.patch.object(plot_tab, "add_params_to_ui")
        mocker.patch.object(plot_tab, "remove_params_from_ui")

        plot_tab.update_params_ui()

        plot_tab.add_params_to_ui.assert_called_with({"c", "d"})
        plot_tab.remove_params_from_ui.assert_called_with({"a", "e"})

    def test_update_params_ui_values_from_model(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        plot_tab.model.get_parameter_names.return_value = ["foo"]
        parameter = mocker.Mock()
        parameter.name = "foo"
        plot_tab.model.get_parameter_by_name.return_value = parameter
        widget = mocker.Mock()
        widget.findChildren.return_value = []
        plot_tab._params["foo"] = widget

        plot_tab.update_params_ui_values_from_model()

        widget.findChild.assert_called()

    def test_update_fit_domain_from_model(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        mocker.patch.object(plot_tab, "fit_domain_area")
        plot_tab.model.get_fit_domain.return_value = sentinel.xmin, sentinel.xmax
        plot_tab.model.get_fit_domain_enabled.return_value = True

        plot_tab.update_fit_domain_from_model()

        plot_tab.ui.fit_start_box.setValue.assert_called_with(sentinel.xmin)
        plot_tab.ui.fit_end_box.setValue.assert_called_with(sentinel.xmax)
        plot_tab.ui.use_fit_domain.setCheckState.assert_called_with(
            QtCore.Qt.CheckState.Checked
        )
        plot_tab.fit_domain_area.setRegion.assert_called_with(
            (sentinel.xmin, sentinel.xmax)
        )

    def test_updated_plot_range_calls_update_model_curves(
        self, plot_tab: PlotTab, mocker: MockerFixture
    ):
        mocker.patch.object(plot_tab, "update_model_curves")
        plot_tab.ui.draw_curve_option.currentIndex.return_value = list(
            DRAW_CURVE_OPTIONS.keys()
        ).index(DrawCurve.ON_AXIS)
        plot_tab.ui.plot_widget.viewRange.return_value = [[0, 10.0], [0, 10.0]]

        plot_tab.updated_plot_range()

        plot_tab.update_model_curves.assert_called()

    def test_get_draw_curve_option(self, plot_tab: PlotModel):
        plot_tab.ui.draw_curve_option.currentIndex.return_value = 0

        option = plot_tab.get_draw_curve_option()

        assert option == DrawCurve.ON_DATA
