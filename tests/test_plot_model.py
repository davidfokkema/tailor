from unittest.mock import Mock, call, sentinel

import lmfit
import numpy as np
import pytest
from numpy.testing import assert_array_equal
from pytest_mock import MockerFixture

from tailor.data_model import DataModel
from tailor.plot_model import Parameter, PlotModel


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

    return PlotModel(
        data_model=data_model,
        x_col="col1",
        y_col="col2",
        x_err_col=None,
        y_err_col=None,
    )


@pytest.fixture()
def simple_data_model():
    data_model = DataModel()
    data_model.insert_columns(0, 3)
    data_model.insert_rows(0, 5)
    data_model.rename_column("col1", "x")
    data_model.rename_column("col2", "y")
    data_model.rename_column("col3", "y_err")
    data_model.set_values_from_array(
        0,
        0,
        np.array(
            [
                [0.0, 0.0, 0.2],
                [1.0, 0.9, 0.2],
                [2.0, 3.7, 0.2],
                [3.0, 9.5, 1.0],
                [4.0, 16.2, 0.2],
            ]
        ),
    )
    return data_model


@pytest.fixture()
def simple_data_no_errors(simple_data_model):
    return PlotModel(
        data_model=simple_data_model,
        x_col="col1",
        y_col="col2",
        x_err_col=None,
        y_err_col=None,
    )


@pytest.fixture()
def simple_data_with_errors(simple_data_model):
    return PlotModel(
        data_model=simple_data_model,
        x_col="col1",
        y_col="col2",
        x_err_col=None,
        y_err_col="col3",
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
        assert model.fit_domain is None
        assert model.use_fit_domain is False
        assert model.best_fit is None
        assert model.fit_data_checksum is None

    def test_init_sets_axis_labels(self, mocker: MockerFixture):
        mocker.patch.object(PlotModel, "get_x_col_name")
        mocker.patch.object(PlotModel, "get_y_col_name")
        data_model = Mock(DataModel)
        data_model.get_column.return_value = [0.0, 0.5, 1.0]

        model = PlotModel(data_model, sentinel.x, sentinel.y, None, None)

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
        model.x_err_col = None
        model.y_err_col = None
        model.data_model.get_column.side_effect = [
            [1, 2],
            [3, 4],
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

    def test_get_data_in_fit_domain(self, simple_data_with_errors: PlotModel):
        simple_data_with_errors.fit_domain = (1.5, 3.5)
        simple_data_with_errors.use_fit_domain = True

        x, y, x_err, y_err = simple_data_with_errors.get_data_in_fit_domain()

        assert x == pytest.approx([2.0, 3.0])
        assert y == pytest.approx([3.7, 9.5])
        assert x_err == pytest.approx(0.0)
        assert y_err == pytest.approx([0.2, 1.0])

    def test_get_data_in_fit_domain_without_fit_domain(
        self, model: PlotModel, mocker: MockerFixture
    ):
        mocker.patch.object(model, "get_data")

        actual = model.get_data_in_fit_domain()

        model.get_data.assert_called()
        assert actual == model.get_data.return_value

    def test_get_data_in_fit_domain_dont_use_fit_domain(
        self, model: PlotModel, mocker: MockerFixture
    ):
        mocker.patch.object(model, "get_data")
        model.fit_domain = (1.5, 3.5)

        actual = model.get_data_in_fit_domain()

        model.get_data.assert_called()
        assert actual == model.get_data.return_value

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
        "x_col, expression, transformed",
        [
            ("col1", "a * x + b", "a * col1 + b"),
            ("col1", "y ** 2 + 2 * x", "y ** 2 + 2 * col1"),
            ("col2", "y + 2 * x", "col2 + 2 * x"),
            ("col3", "x + 2 * z", "x + 2 * col3"),
            ("col1", "x ** 2\n+    2 * z", "col1 ** 2\n+2 * z"),
            ("col1", "x ** 2\n    +2 * z", "col1 ** 2\n+2 * z"),
        ],
    )
    def test_update_model_expression(
        self,
        model: PlotModel,
        mocker: MockerFixture,
        x_col,
        expression,
        transformed,
    ):
        col_names = {"col2": "y", "col3": "z", "col1": "x"}
        mocker.patch.object(model, "update_model_parameters")
        # return column name ('col1' -> 'x')
        model.data_model.get_column_name.return_value = col_names[x_col]
        model.x_col = x_col

        model.update_model_expression(expression)

        model.data_model.get_column_name.assert_called_with(x_col)
        assert model.model_expression == transformed
        assert isinstance(model.model, lmfit.models.ExpressionModel)
        model.update_model_parameters.assert_called()

    def test_update_model_expression_resets_fit_on_changes(
        self, bare_bones_data: PlotModel
    ):
        bare_bones_data.model_expression = "a * col1 + b"
        bare_bones_data.best_fit = sentinel.fit

        bare_bones_data.update_model_expression("a * x")
        assert bare_bones_data.best_fit is None

    def test_update_model_expression_keeps_fit_if_no_changes(
        self, bare_bones_data: PlotModel
    ):
        bare_bones_data.model_expression = "a * col1 + b"
        bare_bones_data.data_model.get_column_name.return_value = "x"
        bare_bones_data.best_fit = sentinel.fit

        bare_bones_data.update_model_expression("a*x+b")
        assert bare_bones_data.best_fit is sentinel.fit

    @pytest.mark.parametrize(
        "expression, transformed",
        [("x + (2 * ", "x + (2 * "), ("a * y + b", "a * y + b")],
    )
    def test_update_broken_model_expression(
        self, bare_bones_data: PlotModel, mocker: MockerFixture, expression, transformed
    ):
        mocker.patch.object(bare_bones_data, "update_model_parameters")
        # first run: create a working model
        bare_bones_data.update_model_expression("a * x")
        bare_bones_data.best_fit = sentinel.fit
        bare_bones_data.update_model_parameters.reset_mock()

        # now see if it breaks correctly (syntax error or missing x)
        bare_bones_data.update_model_expression(expression)

        assert bare_bones_data.model_expression == transformed
        assert bare_bones_data.model is None
        assert bare_bones_data.best_fit is None
        bare_bones_data.update_model_parameters.assert_not_called()

    @pytest.mark.parametrize(
        "x_col, expression, expected",
        [
            ("col2", "col2 ** 2 + 2 * col3", "y ** 2 + 2 * col3"),
            ("col1", "col2 + 2 * col1", "col2 + 2 * x"),
            ("col2", "col2 + 2 * t", "y + 2 * t"),
            ("col2", "col2 ** 2\n+2 * col3", "y ** 2\n+2 * col3"),
            ("col3", "col2 ** 2\n+2 * col3", "col2 ** 2\n+2 * z"),
            ("col1", "x + (2 * ", "x + (2 * "),
        ],
    )
    def test_get_model_expression(self, model: PlotModel, x_col, expression, expected):
        col_names = {"col2": "y", "col3": "z", "col1": "x"}
        model.model_expression = expression
        # return column name ('col1' -> 'x')
        model.data_model.get_column_name.return_value = col_names[x_col]
        model.x_col = x_col

        actual = model.get_model_expression()

        model.data_model.get_column_name.assert_called_with(x_col)
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

    def test_evaluate_model(self, bare_bones_data: PlotModel):
        bare_bones_data.model = lmfit.models.ExpressionModel(
            "a * col1 ** 2 + b", independent_vars=["col1"]
        )
        bare_bones_data.parameters["a"] = Parameter("a", 2.0)
        bare_bones_data.parameters["b"] = Parameter("b", 0.5)
        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        expected = np.array([0.5, 2.5, 8.5, 18.5, 32.5])

        actual = bare_bones_data.evaluate_model(x)

        assert_array_equal(actual, expected)

    def test_evaluate_model_without_model(self, model: PlotModel):
        assert model.evaluate_model(x=[1, 2, 3]) is None

    def test_perform_fit_without_model(self, model: PlotModel):
        model.perform_fit()
        assert model.best_fit is None

    def test_perform_fit_without_errors(self, simple_data_no_errors: PlotModel):
        simple_data_no_errors.update_model_expression("a * x ** 2 + b")

        simple_data_no_errors.perform_fit()

        assert simple_data_no_errors.best_fit.params["a"].value == pytest.approx(
            1.02644, abs=1e-5
        )
        assert simple_data_no_errors.best_fit.params["b"].value == pytest.approx(
            -0.0986207, abs=1e-7
        )

    def test_perform_fit_with_errors(self, simple_data_with_errors: PlotModel):
        simple_data_with_errors.update_model_expression("a * x ** 2 + b")

        simple_data_with_errors.perform_fit()

        assert simple_data_with_errors.best_fit.params["a"].value == pytest.approx(
            1.01856, abs=1e-5
        )
        assert simple_data_with_errors.best_fit.params["b"].value == pytest.approx(
            -0.142706, abs=1e-6
        )

    def test_perform_fit_with_domain(self, simple_data_no_errors: PlotModel):
        simple_data_no_errors.update_model_expression("a * x ** 2 + b")
        simple_data_no_errors.fit_domain = (1.5, 3.5)
        simple_data_no_errors.use_fit_domain = True

        simple_data_no_errors.perform_fit()

        assert simple_data_no_errors.best_fit.params["a"].value == pytest.approx(
            1.16, abs=1e-2
        )
        assert simple_data_no_errors.best_fit.params["b"].value == pytest.approx(
            -0.94, abs=1e-2
        )

    @pytest.mark.filterwarnings("ignore:divide by zero")
    def test_perform_fit_with_nans(self, simple_data_with_errors: PlotModel):
        simple_data_with_errors.update_model_expression("a / x")
        # make sure fit does not crash due to NaNs for x = 0
        simple_data_with_errors.perform_fit()

    def test_perform_fit_saves_checksum(self, model: PlotModel, mocker: MockerFixture):
        # mock everything needed to be able to perform the 'fit'
        mocker.patch.object(model, "model")
        mocker.patch.object(model, "get_data_in_fit_domain")
        mocker.patch.object(model, "hash_data")
        model.x_col = "x"
        y_err = mocker.MagicMock(name="y_err")
        model.get_data_in_fit_domain.return_value = (
            sentinel.x,
            sentinel.y,
            sentinel.x_err,
            y_err,
        )
        model.hash_data.return_value = sentinel.hash

        model.perform_fit()

        assert model.fit_data_checksum == sentinel.hash
        model.hash_data.assert_called_with(
            (sentinel.x, sentinel.y, sentinel.x_err, y_err)
        )

    @pytest.mark.parametrize(
        "data",
        [
            ([1, 2, 3]),
            ([4, 5, 6]),
            ([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]),
        ],
    )
    def test_hash_data_for_identical_data(self, model: PlotModel, data):
        assert model.hash_data(data) == model.hash_data(data)

    @pytest.mark.parametrize(
        "data1, data2",
        [
            ([1, 2, 3], [1, 2, 4]),
            ([4, 5, 6], [5, 5, 6]),
            ([[1, 2], [3, 4]], [[1, 1], [3, 4]]),
        ],
    )
    def test_hash_data_for_nonidentical_data(self, model: PlotModel, data1, data2):
        assert model.hash_data(data1) != model.hash_data(data2)

    def test_verify_best_fit_data_identical(
        self, model: PlotModel, mocker: MockerFixture
    ):
        mocker.patch.object(model, "get_data_in_fit_domain")
        mocker.patch.object(model, "hash_data")
        model.get_data_in_fit_domain.return_value = sentinel.data
        model.hash_data.return_value = sentinel.hash
        model.fit_data_checksum = sentinel.hash
        model.best_fit = sentinel.best_fit

        result = model.verify_best_fit_data()

        assert result is True
        model.hash_data.assert_called_with(sentinel.data)
        assert model.best_fit is sentinel.best_fit
        assert model.fit_data_checksum is sentinel.hash

    def test_verify_best_fit_data_nonidentical(
        self, model: PlotModel, mocker: MockerFixture
    ):
        mocker.patch.object(model, "get_data_in_fit_domain")
        mocker.patch.object(model, "hash_data")
        model.get_data_in_fit_domain.return_value = sentinel.data
        model.hash_data.return_value = sentinel.hash2
        model.fit_data_checksum = sentinel.hash1
        model.best_fit = sentinel.best_fit

        result = model.verify_best_fit_data()

        assert result is False
        model.hash_data.assert_called_with(sentinel.data)
        assert model.best_fit is None
        assert model.fit_data_checksum is None

    def test_evaluate_best_fit(self, bare_bones_data: PlotModel, mocker: MockerFixture):
        mocker.patch.object(bare_bones_data, "best_fit")
        bare_bones_data.best_fit.eval.return_value = sentinel.values

        actual = bare_bones_data.evaluate_best_fit(sentinel.x_values)

        bare_bones_data.best_fit.eval.assert_called_with(col1=sentinel.x_values)
        assert actual == sentinel.values

    def test_evaluate_best_fit_without_fit(self, bare_bones_data: PlotModel):
        assert bare_bones_data.evaluate_best_fit([1, 2, 3]) is None
