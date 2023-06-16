from unittest.mock import Mock, call, sentinel

import numpy as np
import pytest
from pytest_mock import MockerFixture

from tailor.data_model import DataModel
from tailor.plot_model import PlotModel


@pytest.fixture()
def model(mocker: MockerFixture):
    return PlotModel(
        data_model=Mock(spec=DataModel),
        x_col=sentinel.x_col,
        y_col=sentinel.y_col,
        x_err_col=sentinel.x_err_col,
        y_err_col=sentinel.y_err_col,
    )


class TestImplementationDetails:
    def test_init_sets_attributes(self, model: PlotModel):
        assert model.x_col == sentinel.x_col
        assert model.y_col == sentinel.y_col
        assert model.x_err_col == sentinel.x_err_col
        assert model.y_err_col == sentinel.y_err_col
        assert isinstance(model.data_model, DataModel) is True


class TestPlotModel:
    def test_get_data_returns_tuple(self, model: PlotModel):
        model.data_model.get_column.side_effect = [[1, 2], [1, 2], [1, 2], [1, 2]]
        x, y, x_err, y_err = model.get_data()

    def test_get_data_calls_get_column(self, model: PlotModel):
        model.data_model.get_column.side_effect = [[1, 2], [1, 2], [1, 2], [1, 2]]
        data = model.get_data()

        expected = [
            call(sentinel.x_col),
            call(sentinel.y_col),
            call(sentinel.x_err_col),
            call(sentinel.y_err_col),
        ]
        assert model.data_model.get_column.call_args_list == expected

    def test_get_data_returns_correct_columns(self, model: PlotModel):
        x_ = [1, 2]
        y_ = [3, 4]
        x_err_ = [5, 6]
        y_err_ = [7, 8]
        model.data_model.get_column.side_effect = [x_, y_, x_err_, y_err_]

        x, y, x_err, y_err = model.get_data()

        assert x == pytest.approx(x_)
        assert y == pytest.approx(y_)
        assert x_err == pytest.approx(x_err_)
        assert y_err == pytest.approx(y_err_)

    def test_get_data_without_error_values(self, model: PlotModel):
        model.data_model.get_column.side_effect = [
            [1, 2],
            [3, 4],
            KeyError,
            KeyError,
        ]

        _, _, x_err, y_err = model.get_data()

        assert x_err == pytest.approx(0.0)
        assert y_err == pytest.approx(0.0)

    def test_get_data_drops_nans(self, model: PlotModel):
        model.data_model.get_column.side_effect = [
            np.array([np.nan, 1, 2, 3, 4, 5]),
            np.array([0, np.nan, 2, 3, 4, 5]),
            np.array([0, 1, 2, np.nan, 4, 5]),
            np.array([0, 1, 2, 3, np.nan, 5]),
        ]

        x, y, x_err, y_err = model.get_data()

        assert x == pytest.approx([2.0, 5.0])
        assert y == pytest.approx([2.0, 5.0])
        assert x_err == pytest.approx([2.0, 5.0])
        assert y_err == pytest.approx([2.0, 5.0])

    def test_get_limits_from_data(self, model: PlotModel, mocker: MockerFixture):
        mocker.patch.object(model, "get_data").return_value = [
            np.array([1.0, 3.0]),
            np.array([4.0, 5.0]),
            np.array([0.5, 1.0]),
            np.array([1.0, 0.5]),
        ]

        x_min, x_max, y_min, y_max = model.get_limits_from_data(padding=0.0)

        assert x_min == pytest.approx(0.5)
        assert x_max == pytest.approx(4.0)
        assert y_min == pytest.approx(3.0)
        assert y_max == pytest.approx(5.5)

    def test_get_limits_from_data_with_padding(
        self, model: PlotModel, mocker: MockerFixture
    ):
        mocker.patch.object(model, "get_data").return_value = [
            np.array([1.0, 3.0]),
            np.array([4.0, 5.0]),
            0.0,
            0.0,
        ]

        x_min, x_max, y_min, y_max = model.get_limits_from_data(padding=0.5)

        assert x_min == pytest.approx(0.0)
        assert x_max == pytest.approx(4.0)
        assert y_min == pytest.approx(3.5)
        assert y_max == pytest.approx(5.5)
