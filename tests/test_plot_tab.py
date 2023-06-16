from unittest.mock import Mock, sentinel

import pytest
from pytest_mock import MockerFixture

import tailor.plot_tab
from tailor.data_sheet import DataSheet
from tailor.plot_model import PlotModel
from tailor.plot_tab import PlotTab


@pytest.fixture()
def plot_tab(mocker: MockerFixture):
    mocker.patch.object(tailor.plot_tab, "PlotModel")
    mocker.patch.object(PlotTab, "connect_ui_events")
    return PlotTab(
        Mock(spec=DataSheet),
        sentinel.x_col,
        sentinel.y_col,
        sentinel.x_err_col,
        sentinel.y_err_col,
    )


class TestImplementationDetails:
    def test_init_sets_attributes(self, mocker: MockerFixture):
        PlotModel_ = mocker.patch.object(tailor.plot_tab, "PlotModel")
        mock_data_sheet = Mock(spec=DataSheet)
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

    def test_init_calls_setup(self, plot_tab: PlotTab):
        plot_tab.connect_ui_events.assert_called_once()
