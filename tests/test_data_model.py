from unittest.mock import sentinel

import numpy as np
import pandas as pd
import pytest
from PySide6 import QtCore
from pytest_mock import MockerFixture

from tailor.data_model import DataModel
from tailor.qdata_model import QDataModel


@pytest.fixture()
def model():
    return DataModel()


@pytest.fixture()
def qmodel(mocker: MockerFixture):
    model = QDataModel()
    for attr in dir(DataModel):
        if not attr.startswith("__"):
            mocker.patch.object(model, attr)
    return model


@pytest.fixture()
def bare_bones_data():
    """Create a bare bones data model.

    This is an instance of QDataModel with a very basic data structure (five
    rows, two columns) and an updated column number variable, but nothing else.
    You can use this to test basic data manipulation required by Qt for
    subclasses of QAbstractDataModel.

    This fixture depends on certain implementation details.
    """
    qmodel = QDataModel()
    qmodel._data = pd.DataFrame.from_dict(
        {
            "col0": [1.0, 2.0, 3.0, 4.0, 5.0],
            "col1": [6.0, 7.0, 8.0, 9.0, 10.0],
            "col2": [11.0, 12.0, 13.0, 14.0, 15.0],
        }
    )
    qmodel._new_col_num += 3
    return qmodel


class TestImplementationDetails:
    def test_instance(self):
        assert issubclass(QDataModel, DataModel)

    def test_model_attributes(self, model: DataModel):
        assert type(model._data) == pd.DataFrame
        assert model._new_col_num == 0

    def test_new_column_label(self, model: DataModel):
        labels = [model._create_new_column_label() for _ in range(3)]
        assert labels == ["col1", "col2", "col3"]
        assert model._new_col_num == 3


class TestQtRequired:
    def test_rowCount(self, qmodel: QDataModel):
        assert qmodel.rowCount() == qmodel.num_rows.return_value

    def test_rowCount_valid_parent(self, qmodel: QDataModel):
        """Valid parent has no children in a table."""
        index = qmodel.createIndex(0, 0)
        assert qmodel.rowCount(index) == 0

    def test_columnCount(self, qmodel: QDataModel):
        assert qmodel.columnCount() == qmodel.num_columns.return_value

    def test_columnCount_valid_parent(self, qmodel: QDataModel):
        """Valid parent has no children in a table."""
        index = qmodel.createIndex(0, 0)
        assert qmodel.columnCount(index) == 0

    @pytest.mark.parametrize(
        "row, column, is_calculated, value, expected, role",
        [
            (0, 0, False, 0.0, "0", None),
            (0, 0, True, 0.0, "0", None),
            (0, 0, False, np.nan, "", None),
            (0, 0, True, np.nan, "nan", None),
            (3, 4, False, 1.23456, "1.23456", None),
            (2, 1, False, 4.2, "4.2", QtCore.Qt.DisplayRole),
            (1, 7, False, 3.7, "3.7", QtCore.Qt.EditRole),
        ],
    )
    def test_data_returns_data(
        self,
        qmodel: QDataModel,
        row,
        column,
        is_calculated,
        value,
        expected,
        role,
    ):
        index = qmodel.createIndex(row, column)
        qmodel.get_value.return_value = value
        qmodel.is_calculated_column.return_value = is_calculated

        if not role:
            actual = qmodel.data(index)
        else:
            actual = qmodel.data(index, role)

        qmodel.get_value.assert_called_once_with(row, column)
        assert actual == expected

    def test_data_returns_None_for_invalid_role(self, qmodel: QDataModel):
        index = qmodel.createIndex(2, 1)
        value = qmodel.data(index, QtCore.Qt.DecorationRole)
        assert value is None

    def test_headerData_for_columns(self, qmodel: QDataModel):
        actual = qmodel.headerData(sentinel.colidx, QtCore.Qt.Horizontal)

        qmodel.get_column_name.assert_called_once_with(sentinel.colidx)
        assert actual == qmodel.get_column_name.return_value

    @pytest.mark.parametrize("rowidx, expected", [(0, 1), (1, 2), (7, 8), (20, 21)])
    def test_headerData_for_rows(self, qmodel: QDataModel, rowidx, expected):
        actual = qmodel.headerData(rowidx, QtCore.Qt.Vertical)
        assert actual == expected

    def test_headerData_returns_None_for_invalid_role(self, qmodel: QDataModel):
        # Decoration role is not supported
        assert (
            qmodel.headerData(0, QtCore.Qt.Horizontal, QtCore.Qt.DecorationRole) is None
        )

    @pytest.mark.parametrize("role", [None, QtCore.Qt.EditRole])
    def test_setData(self, qmodel: QDataModel, mocker: MockerFixture, role):
        mocker.patch.object(qmodel, "dataChanged")
        index = qmodel.createIndex(1, 2)

        if role:
            qmodel.setData(index, 3, role)
        else:
            qmodel.setData(index, 3)

        qmodel.set_value.assert_called_once_with(1, 2, 3.0)
        qmodel.dataChanged.emit.assert_called_once_with(index, index)

    def test_setData_with_unsupported_role(self, qmodel: QDataModel):
        index = qmodel.createIndex(2, 1)
        retvalue = qmodel.setData(index, 5.0, QtCore.Qt.DecorationRole)
        assert retvalue is False

    @pytest.mark.parametrize("is_calculated", [True, False])
    def test_flags(self, qmodel: QDataModel, is_calculated):
        qmodel.is_calculated_column.return_value = is_calculated
        expected = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if not is_calculated:
            expected |= QtCore.Qt.ItemIsEditable

        index = qmodel.createIndex(2, 123)
        flags = qmodel.flags(index)

        qmodel.is_calculated_column.assert_called_once_with(123)
        assert flags == expected

    def test_insertRows(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "beginInsertRows")
        mocker.patch.object(qmodel, "endInsertRows")
        parent = QtCore.QModelIndex()
        retvalue1 = qmodel.insertRows(3, 4, parent=parent)

        qmodel.insert_rows.assert_called_once_with(3, 4)
        assert retvalue1 is True
        # four rows: 3 (first), 4, 5, 6 (last)
        qmodel.beginInsertRows.assert_called_with(parent, 3, 6)
        qmodel.endInsertRows.assert_called()

    def test_insertRows_valid_parent(self, qmodel: QDataModel):
        """You can't add rows inside cells."""
        assert qmodel.insertRows(0, 2, parent=qmodel.createIndex(0, 0)) is False

    def test_insertRows_no_parent(self, qmodel: QDataModel):
        assert qmodel.insertRows(3, 4) is True

    def test_removeRows(self, qmodel: QDataModel, mocker: MockerFixture):
        # WIP: test that begin/endRemoveRows is called
        mocker.patch.object(qmodel, "beginRemoveRows")
        mocker.patch.object(qmodel, "endRemoveRows")
        parent = QtCore.QModelIndex()
        retvalue = qmodel.removeRows(3, 4, parent=parent)

        qmodel.remove_rows.assert_called_once_with(3, 4)
        assert retvalue is True
        # four rows: 3 (first), 4, 5, 6 (last)
        qmodel.beginRemoveRows.assert_called_with(parent, 3, 6)
        qmodel.endRemoveRows.assert_called()

    def test_removeRows_valid_parent(self, qmodel: QDataModel):
        """You can't remove rows inside cells."""
        assert qmodel.removeRows(0, 2, parent=qmodel.createIndex(0, 0)) is False

    def test_removeRows_no_parent(self, qmodel: QDataModel):
        assert qmodel.removeRows(3, 4) is True

    def test_insertColumns(self, bare_bones_data: QDataModel):
        retvalue = bare_bones_data.insertColumns(1, 2)
        assert retvalue is True
        assert bare_bones_data._data.shape == (5, 5)
        assert list(bare_bones_data._data.iloc[0]) == pytest.approx(
            [1.0, np.nan, np.nan, 6.0, 11.0], nan_ok=True
        )

    def test_insertColumns_valid_parent(self, bare_bones_data: QDataModel):
        """You can't add columns inside cells."""
        assert (
            bare_bones_data.insertColumns(
                0, 2, parent=bare_bones_data.createIndex(0, 0)
            )
            is False
        )

    def test_removeColumns(self, bare_bones_data: QDataModel):
        retvalue = bare_bones_data.removeColumns(1, 2)
        assert retvalue is True
        assert bare_bones_data._data.shape == (5, 1)
        assert bare_bones_data._data.columns == ["col0"]

    def test_removeColumns_valid_parent(self, bare_bones_data: QDataModel):
        """You can't remove columns inside cells."""
        assert (
            bare_bones_data.removeColumns(
                0, 2, parent=bare_bones_data.createIndex(0, 0)
            )
            is False
        )


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
