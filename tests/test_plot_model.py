from unittest.mock import Mock, call, sentinel

import lmfit
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


@pytest.fixture()
def bare_bones_data(mocker: MockerFixture):
    data_model = Mock(spec=DataModel)
    data_model._col_names = {"col2": "y", "col3": "z", "col1": "x"}
    data_model.get_column_names.return_value = data_model._col_names.values()

    return PlotModel(
        data_model=data_model,
        x_col="col1",
        y_col="col2",
        x_err_col=None,
        y_err_col=None,
    )


class TestImplementationDetails:
    def test_init_sets_attributes(self, model: PlotModel):
        assert model.x_col == sentinel.x_col
        assert model.y_col == sentinel.y_col
        assert model.x_err_col == sentinel.x_err_col
        assert model.y_err_col == sentinel.y_err_col
        assert isinstance(model.data_model, DataModel)
        assert isinstance(model.model_expression, str)
        assert isinstance(model.parameters, dict)

    def test_init_sets_axis_labels(self, mocker: MockerFixture):
        mocker.patch.object(PlotModel, "get_x_col_name")
        mocker.patch.object(PlotModel, "get_y_col_name")

        model = PlotModel(None, sentinel.x, sentinel.y, None, None)

        assert model.x_label == model.get_x_col_name.return_value
        assert model.y_label == model.get_y_col_name.return_value


class TestPlotModel:
    def test_get_x_col_name(self, model: PlotModel):
        name = model.get_x_col_name()
        assert name == model.data_model.get_column_name.return_value
        model.data_model.get_column_name.assert_called_with(sentinel.x_col)

    def test_get_y_col_name(self, model: PlotModel):
        name = model.get_y_col_name()
        assert name == model.data_model.get_column_name.return_value
        model.data_model.get_column_name.assert_called_with(sentinel.y_col)

    def test_get_x_err_col_name(self, model: PlotModel):
        name = model.get_x_err_col_name()
        assert name == model.data_model.get_column_name.return_value
        model.data_model.get_column_name.assert_called_with(sentinel.x_err_col)

    def test_get_x_err_col_name_without_errors(self, model: PlotModel):
        model.data_model.get_column_name.side_effect = KeyError
        assert model.get_x_err_col_name() is None

    def test_get_y_err_col_name(self, model: PlotModel):
        name = model.get_y_err_col_name()
        assert name == model.data_model.get_column_name.return_value
        model.data_model.get_column_name.assert_called_with(sentinel.y_err_col)

    def test_get_y_err_col_name_without_errors(self, model: PlotModel):
        model.data_model.get_column_name.side_effect = KeyError
        assert model.get_y_err_col_name() is None

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

        # without error values, should return 0.0
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

    @pytest.mark.parametrize(
        "expression, transformed",
        [
            ("a * x + b", "a * col1 + b"),
            ("y ** 2 + 2 * x", "col2 ** 2 + 2 * col1"),
            ("y + 2 * x", "col2 + 2 * col1"),
            ("x + 2 * t", "col1 + 2 * t"),
            ("x ** 2\n+    2 * z", "col1 ** 2\n+2 * col3"),
            ("x ** 2\n    +2 * z", "col1 ** 2\n+2 * col3"),
        ],
    )
    def test_update_model_expression(
        self, bare_bones_data: PlotModel, mocker: MockerFixture, expression, transformed
    ):
        mocker.patch.object(bare_bones_data, "update_model_parameters")
        bare_bones_data.update_model_expression(expression)
        assert bare_bones_data.model_expression == transformed
        assert isinstance(bare_bones_data.model, lmfit.models.ExpressionModel)
        bare_bones_data.update_model_parameters.assert_called()

    @pytest.mark.parametrize(
        "expression, transformed",
        [("x + (2 * ", "x + (2 * "), ("a * y + b", "a * col2 + b")],
    )
    def test_update_broken_model_expression(
        self, bare_bones_data: PlotModel, mocker: MockerFixture, expression, transformed
    ):
        mocker.patch.object(bare_bones_data, "update_model_parameters")
        # first run: create a working model
        bare_bones_data.update_model_expression("a * x")
        bare_bones_data.update_model_parameters.reset_mock()

        # now see if it breaks correctly
        bare_bones_data.update_model_expression(expression)

        assert bare_bones_data.model_expression == transformed
        assert bare_bones_data.model is None
        bare_bones_data.update_model_parameters.assert_not_called()

    @pytest.mark.parametrize(
        "expression, expected",
        [
            ("col2 ** 2 + 2 * col3", "y ** 2 + 2 * z"),
            ("col2 + 2 * col1", "y + 2 * x"),
            ("col2 + 2 * t", "y + 2 * t"),
            ("col2 ** 2\n+2 * col3", "y ** 2\n+2 * z"),
            ("col2 ** 2\n+2 * col3", "y ** 2\n+2 * z"),
            ("x + (2 * ", "x + (2 * "),
        ],
    )
    def test_get_model_expression(self, model: PlotModel, expression, expected):
        model.data_model._col_names = {"col2": "y", "col3": "z", "col1": "x"}
        model.model_expression = expression

        actual = model.get_model_expression()

        assert actual == expected

    @pytest.mark.parametrize("extra", [{}, {"d": sentinel.d}])
    def test_update_model_parameters(self, bare_bones_data: PlotModel, extra):
        bare_bones_data.model = lmfit.models.ExpressionModel(
            "a * x ** 2 + b * x + c", independent_vars=["x"]
        )
        bare_bones_data.parameters = {"a": sentinel.a, "b": sentinel.b} | extra

        bare_bones_data.update_model_parameters()

        assert set(bare_bones_data.parameters.keys()) == {"a", "b", "c"}
        assert bare_bones_data.parameters["a"] == sentinel.a
        assert bare_bones_data.parameters["b"] == sentinel.b
