from unittest.mock import sentinel

import numpy as np
import pandas as pd
import pytest
from pytest_mock import MockerFixture

from tailor.data_model import DataModel


@pytest.fixture()
def model():
    return DataModel()


@pytest.fixture()
def bare_bones_data(model: DataModel):
    """Create a bare bones data model.

    This is an instance of QDataModel with a very basic data structure (five
    rows, two columns) and an updated column number variable, but nothing else.
    You can use this to test basic data manipulation required by Qt for
    subclasses of QAbstractDataModel.

    This fixture depends on certain implementation details.
    """
    model._data = pd.DataFrame.from_dict(
        {
            "col1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "col2": [6.0, 7.0, 8.0, 9.0, 10.0],
            "col3": [11.0, 12.0, 13.0, 14.0, 15.0],
        }
    )
    model._col_names = {"col1": "x", "col2": "y", "col3": "z"}
    model._calculated_column_expression["col3"] = "y + 5"
    model._is_calculated_column_valid["col3"] = True
    model._new_col_num += 3
    return model


class TestImplementationDetails:
    def test_model_attributes(self, model: DataModel):
        assert type(model._data) == pd.DataFrame
        assert model._new_col_num == 0

    def test_new_column_label(self, model: DataModel):
        labels = [model._create_new_column_label() for _ in range(3)]
        assert labels == ["col1", "col2", "col3"]
        assert model._new_col_num == 3


class TestDataModel:
    def test_num_rows_row_count(self, bare_bones_data: DataModel):
        assert bare_bones_data.num_rows() == 5

    def test_num_columns(self, bare_bones_data: DataModel):
        assert bare_bones_data.num_columns() == 3

    def test_data_returns_data(self, bare_bones_data: DataModel):
        assert bare_bones_data.get_value(2, 1) == 8.0
        assert bare_bones_data.get_value(3, 0) == 4.0

    @pytest.mark.parametrize("value", [4.7, np.nan])
    def test_set_value(self, bare_bones_data: DataModel, value):
        bare_bones_data.set_value(2, 1, value)
        assert bare_bones_data.get_value(2, 1) == pytest.approx(value, nan_ok=True)

    def test_insert_rows(self, bare_bones_data: DataModel):
        bare_bones_data.insert_rows(3, 4)
        # check that all values in inserted rows are NaN
        # use loc to check that the row labels are reindexed
        assert bool(bare_bones_data._data.loc[3:6].isna().all(axis=None)) is True
        # check insertion using values from col0
        assert list(bare_bones_data._data["col1"]) == pytest.approx(
            [
                1.0,
                2.0,
                3.0,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                4.0,
                5.0,
            ],
            nan_ok=True,
        )

    def test_remove_rows(self, bare_bones_data: DataModel):
        bare_bones_data.remove_rows(1, 2)
        assert list(bare_bones_data._data["col1"]) == pytest.approx([1.0, 4.0, 5.0])
        assert list(bare_bones_data._data["col2"]) == pytest.approx([6.0, 9.0, 10.0])
        assert list(bare_bones_data._data.index) == list(range(3))

    def test_insert_columns(self, bare_bones_data: DataModel):
        bare_bones_data.insert_columns(1, 2)
        assert bare_bones_data._data.shape == (5, 5)
        assert list(bare_bones_data._data.iloc[0]) == pytest.approx(
            [1.0, np.nan, np.nan, 6.0, 11.0], nan_ok=True
        )

    def test_insert_columns_labels(self, bare_bones_data: DataModel):
        bare_bones_data.insert_columns(3, 2)
        assert list(bare_bones_data._data.columns) == [
            "col1",
            "col2",
            "col3",
            "col4",
            "col5",
        ]

    def test_insert_columns_names(self, bare_bones_data: DataModel):
        assert "col4" not in bare_bones_data._col_names
        bare_bones_data.insert_columns(0, 1)
        assert bare_bones_data._col_names["col4"] == "col4"

    def test_remove_columns(self, bare_bones_data: DataModel):
        bare_bones_data.remove_columns(1, 2)
        assert bare_bones_data._data.shape == (5, 1)
        assert bare_bones_data._data.columns == ["col1"]

    def test_remove_columns_removes_calculated_column(self, bare_bones_data: DataModel):
        bare_bones_data.remove_columns(column=0, count=1)
        assert len(bare_bones_data._calculated_column_expression) == 1

        bare_bones_data.remove_columns(column=1, count=1)
        assert len(bare_bones_data._calculated_column_expression) == 0

    def test_remove_columns_calls_recalculate(
        self, bare_bones_data: DataModel, mocker: MockerFixture
    ):
        mocker.patch.object(bare_bones_data, "recalculate_all_columns")
        bare_bones_data.remove_columns(1, 1)
        bare_bones_data.recalculate_all_columns.assert_called()

    @pytest.mark.parametrize(
        "source, dest, order",
        [
            (1, 1, ["col1", "col2", "col3"]),
            (0, 1, ["col2", "col1", "col3"]),
            (0, 2, ["col2", "col3", "col1"]),
            (2, 1, ["col1", "col3", "col2"]),
        ],
    )
    def test_move_column(self, bare_bones_data: DataModel, source, dest, order):
        bare_bones_data.move_column(source, dest)
        assert list(bare_bones_data._data.columns) == order

    def test_insert_calculated_column(self, bare_bones_data: DataModel):
        assert len(bare_bones_data._calculated_column_expression) == 1
        assert bare_bones_data._data.shape == (5, 3)

        bare_bones_data.insert_calculated_column(column=1)

        assert len(bare_bones_data._calculated_column_expression) == 2
        assert bare_bones_data._data.shape == (5, 4)
        assert list(bare_bones_data._data.iloc[0]) == pytest.approx(
            [1.0, np.nan, 6.0, 11.0], nan_ok=True
        )

    def test_insert_calculated_column_sets_attributes(
        self, bare_bones_data: DataModel, mocker: MockerFixture
    ):
        mocker.patch.object(bare_bones_data, "insert_columns")
        bare_bones_data.insert_columns.return_value = [sentinel.label]

        bare_bones_data.insert_calculated_column(column=1)

        assert bare_bones_data._calculated_column_expression[sentinel.label] is None
        assert bare_bones_data._is_calculated_column_valid[sentinel.label] is False

    def test_get_column_label(self, bare_bones_data: DataModel):
        expected = ["col1", "col2", "col3"]
        actual = [bare_bones_data.get_column_label(idx) for idx in range(3)]
        assert actual == expected

    def test_get_column_name(self, bare_bones_data: DataModel):
        labels = ["col1", "col2", "col3"]
        expected = ["x", "y", "z"]
        actual = [bare_bones_data.get_column_name(label) for label in labels]
        assert actual == expected

    def test_get_column(self, bare_bones_data: DataModel):
        expected = [6.0, 7.0, 8.0, 9.0, 10.0]
        actual = bare_bones_data.get_column("col2")
        assert isinstance(actual, np.ndarray)
        assert list(actual) == pytest.approx(expected)

    def test_rename_column(self, bare_bones_data: DataModel):
        bare_bones_data.rename_column("col1", "t null")
        # rewrites spaces to underscores
        assert bare_bones_data.get_column_name("col1") == "t_null"

    def test_normalize_column_name(self, model: DataModel):
        assert model.normalize_column_name("t x y") == "t_x_y"
        assert model.normalize_column_name("  x") == "__x"
        assert model.normalize_column_name("x  ") == "x__"
        assert model.normalize_column_name("1x") == "_1x"

    def test_is_calculated_column(self, bare_bones_data: DataModel):
        assert bare_bones_data.is_calculated_column("col1") is False
        assert bare_bones_data.is_calculated_column("col3") is True

    def test_is_column_valid(self, bare_bones_data: DataModel):
        # not calculated
        assert bare_bones_data.is_column_valid("col1") is True
        # calculated, valid
        assert bare_bones_data.is_calculated_column("col3") is True
        assert bare_bones_data.is_column_valid("col3") is True
        # just added, not yet a valid expression
        bare_bones_data.insert_calculated_column(0)
        assert bare_bones_data.is_calculated_column("col4") is True
        assert bare_bones_data.is_column_valid("col4") is False
