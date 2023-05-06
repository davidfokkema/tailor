import pandas as pd
import pytest

from tailor.data_model import DataModel


@pytest.fixture()
def model():
    yield DataModel()


@pytest.fixture()
def data(model: DataModel):
    model.insertColumn(column=0, column_name="x", values=[1, 2, 3, 4])
    model.insertColumn(column=1, column_name="y", values=[1, 4, 9, 16])


def test_data_is_dataframe(model: DataModel):
    assert type(model._data) == pd.DataFrame


def test_adding_data(model: DataModel):
    model.insertColumn(column=0, column_name="x", values=[1, 2, 3, 4])
    assert list(model._data["x"]) == [1, 2, 3, 4]


def test_column_insert_position(data: DataModel):
    pass
