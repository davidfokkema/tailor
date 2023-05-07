import numpy as np
import pandas as pd
import pytest

from tailor.data_model import DataModel


@pytest.fixture()
def model():
    yield DataModel()


def test_data_is_dataframe(model: DataModel):
    assert type(model._data) == pd.DataFrame


def test_adding_data(model: DataModel):
    model.insertColumn(column=0, column_name="x", values=[1, 2, 3, 4])
    assert list(model._data["x"]) == [1, 2, 3, 4]


@pytest.fixture()
def data(model: DataModel):
    model.insertColumn(column=0, column_name="x", values=[1, 2, 3, 4])
    model.insertColumn(column=1, column_name="y", values=[1, 4, 9, 16])
    yield model


def test_adding_default_nan(data: DataModel):
    data.insertColumn(column=0, column_name="foo")
    assert data._data["foo"].isna().all()


def test_column_insert_position(data: DataModel):
    # insert in the middle...
    data.insertColumn(column=1, column_name="s")
    # and at the end.
    data.insertColumn(column=3, column_name="t")
    assert list(data._data.columns) == ["x", "s", "y", "t"]


class TestQtRequired:
    def test_rowCount(self):
        pytest.skip()

    def test_columnCount(self):
        pytest.skip()

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

    def test_removeColumns(self):
        pytest.skip()


# class TestTailorAPI:
#     def test_insert_calculated_column
#       etc.
