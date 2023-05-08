import numpy as np
import pandas as pd
import pytest
from PySide6 import QtCore

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
        {"col0": [1.0, 2.0, 3.0, 4.0, 5.0], "col1": [6.0, 7.0, 8.0, 9.0, 10.0]}
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

    def test_data_returns_data(self, bare_bones_data: DataModel):
        index1 = bare_bones_data.createIndex(2, 1)
        index2 = bare_bones_data.createIndex(3, 0)

        value0 = bare_bones_data.data(index1)
        value1 = bare_bones_data.data(index1, QtCore.Qt.DisplayRole)
        value2 = bare_bones_data.data(index2, QtCore.Qt.EditRole)

        assert value0 == "8"
        assert value1 == "8"
        assert value2 == "4"

    def test_data_returns_None_for_invalid_role(self, bare_bones_data: DataModel):
        index = bare_bones_data.createIndex(2, 1)
        value = bare_bones_data.data(index, QtCore.Qt.DecorationRole)
        assert value is None

    def test_headerData(self, bare_bones_data: DataModel):
        assert bare_bones_data.headerData(0, QtCore.Qt.Horizontal) == "col0"
        assert (
            bare_bones_data.headerData(1, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole)
            == "col1"
        )
        assert (
            bare_bones_data.headerData(
                0, QtCore.Qt.Horizontal, QtCore.Qt.DecorationRole
            )
            is None
        )
        assert bare_bones_data.headerData(3, QtCore.Qt.Vertical) == "4"

    def test_setData(self, bare_bones_data: DataModel):
        # WIP: test that this method emits dataChanged
        index1 = bare_bones_data.createIndex(2, 1)
        index2 = bare_bones_data.createIndex(3, 0)

        retvalue1 = bare_bones_data.setData(index1, 1.7, QtCore.Qt.EditRole)
        retvalue2 = bare_bones_data.setData(index2, 4.2)
        retvalue3 = bare_bones_data.setData(index2, 5.0, QtCore.Qt.DecorationRole)

        assert retvalue1 == retvalue2 is True
        assert retvalue3 is False
        assert bare_bones_data._data.at[2, "col1"] == 1.7
        assert bare_bones_data._data.at[3, "col0"] == 4.2

    def test_flags(self, bare_bones_data: DataModel):
        index = bare_bones_data.createIndex(2, 1)
        flags = bare_bones_data.flags(index)
        assert (
            flags
            == QtCore.Qt.ItemIsEnabled
            | QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsEditable
        )

    def test_insertRows(self, bare_bones_data: DataModel):
        # WIP: test that begin/endInsertRows is called
        retvalue1 = bare_bones_data.insertRows(3, 4, parent=QtCore.QModelIndex())
        assert retvalue1 is True
        # check that all values are in inserted rows are NaN
        # use loc to check that the row labels are reindexed
        assert bool(bare_bones_data._data.loc[3:6].isna().all(axis=None)) is True
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

    def test_insertRows_valid_parent(self, bare_bones_data: DataModel):
        """You can't add rows inside cells."""
        assert (
            bare_bones_data.insertRows(0, 2, parent=bare_bones_data.createIndex(0, 0))
            is False
        )

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
