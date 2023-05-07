import numpy as np
import pandas as pd
import pytest

from tailor.data_model import DataModel


@pytest.fixture()
def model():
    yield DataModel()


@pytest.fixture()
def bare_bones_data(model: DataModel):
    """Create a bare bones data model.

    This is an instance of DataModel with a very basic data structure (five
    rows, two columns) and an updated column number variable, but nothing else.
    You can use this to test basic data manipulation required by Qt for
    subclasses of QAbstractDataModel.

    This fixture depends on certain implementation details.
    """
    model._data = pd.DataFrame.from_dict(
        {"col0": [1, 2, 3, 4, 5], "col1": [6, 7, 8, 9, 10]}
    )
    model._new_col_num += 2
    yield model


class TestImplementationDetails:
    def test_model_attributes(self, model: DataModel):
        assert type(model._data) == pd.DataFrame
        assert model._new_col_num == 0


# def test_adding_data(model: DataModel):
#     model.insertColumn(column=0, column_name="x", values=[1, 2, 3, 4])
#     assert list(model._data["x"]) == [1, 2, 3, 4]


# def test_adding_default_nan(data: DataModel):
#     data.insertColumn(column=0, column_name="foo")
#     assert data._data["foo"].isna().all()


class TestQtRequired:
    def test_rowCount_row_count(self, bare_bones_data: DataModel):
        assert bare_bones_data.rowCount() == 5

    def test_rowCount_valid_parent(self, bare_bones_data: DataModel):
        """Valid parent has no children in a table."""
        index = bare_bones_data.createIndex(0, 0)
        assert bare_bones_data.rowCount(index) == 0

    def test_columnCount(self, bare_bones_data: DataModel):
        assert bare_bones_data.columnCount() == 2

    def test_columnCount_valid_parent(self, bare_bones_data: DataModel):
        """Valid parent has no children in a table."""
        index = bare_bones_data.createIndex(0, 0)
        assert bare_bones_data.columnCount(index) == 0

    def test_data(self):
        pytest.skip()

    def test_headerData(self):
        pytest.skip()

    def test_setData(self):
        pytest.skip()

    def test_flags(self):
        pytest.skip()

    def test_insertRows(self):
        pytest.skip()

    def test_removeRows(self):
        pytest.skip()

    def test_insertColumns(self):
        pytest.skip()

    # def test_column_insert_position(self, data: DataModel):
    #     # insert in the middle...
    #     data.insertColumn(column=1, column_name="s")
    #     # and at the end.
    #     data.insertColumn(column=3, column_name="t")
    #     assert list(data._data.columns) == ["x", "s", "y", "t"]

    def test_removeColumns(self):
        pytest.skip()


# class TestTailorAPI:
#     def test_insert_calculated_column
#       etc.
