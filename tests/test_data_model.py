import numpy as np
import pandas as pd
import pytest

from tailor.data_model import DataModel


@pytest.fixture()
def model():
    return DataModel()


@pytest.fixture()
def bare_bones_data(model):
    """Create a bare bones data model.

    This is an instance of QDataModel with a very basic data structure (five
    rows, two columns) and an updated column number variable, but nothing else.
    You can use this to test basic data manipulation required by Qt for
    subclasses of QAbstractDataModel.

    This fixture depends on certain implementation details.
    """
    model._data = pd.DataFrame.from_dict(
        {
            "col0": [1.0, 2.0, 3.0, 4.0, 5.0],
            "col1": [6.0, 7.0, 8.0, 9.0, 10.0],
            "col2": [11.0, 12.0, 13.0, 14.0, 15.0],
        }
    )
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

    @pytest.mark.parametrize("colidx, name", [(0, "col0"), (1, "col1"), (2, "col2")])
    def test_get_column_name(self, bare_bones_data: DataModel, colidx, name):
        assert bare_bones_data.get_column_name(colidx) == name

    def test_insert_rows(self, bare_bones_data: DataModel):
        bare_bones_data.insert_rows(3, 4)
        # check that all values in inserted rows are NaN
        # use loc to check that the row labels are reindexed
        assert bool(bare_bones_data._data.loc[3:6].isna().all(axis=None)) is True
        # check insertion using values from col0
        assert list(bare_bones_data._data["col0"]) == pytest.approx(
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
        assert list(bare_bones_data._data["col0"]) == pytest.approx([1.0, 4.0, 5.0])
        assert list(bare_bones_data._data["col1"]) == pytest.approx([6.0, 9.0, 10.0])
        assert list(bare_bones_data._data.index) == list(range(3))

    def test_insert_columns(self, bare_bones_data: DataModel):
        bare_bones_data.insert_columns(1, 2)
        assert bare_bones_data._data.shape == (5, 5)
        assert list(bare_bones_data._data.iloc[0]) == pytest.approx(
            [1.0, np.nan, np.nan, 6.0, 11.0], nan_ok=True
        )

    def test_remove_columns(self, bare_bones_data: DataModel):
        bare_bones_data.remove_columns(1, 2)
        assert bare_bones_data._data.shape == (5, 1)
        assert bare_bones_data._data.columns == ["col0"]

    @pytest.mark.parametrize(
        "source, dest, order",
        [
            (1, 1, ["col0", "col1", "col2"]),
            (0, 1, ["col1", "col0", "col2"]),
            (0, 2, ["col1", "col2", "col0"]),
            (2, 1, ["col0", "col2", "col1"]),
        ],
    )
    def test_move_column(self, bare_bones_data: DataModel, source, dest, order):
        bare_bones_data.move_column(source, dest)
        assert list(bare_bones_data._data.columns) == order
