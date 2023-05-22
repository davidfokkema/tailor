from unittest.mock import sentinel

import numpy as np
import pandas as pd
import pytest
from PySide6 import QtCore
from pytest_mock import MockerFixture

from tailor.data_model import DataModel
from tailor.qdata_model import QDataModel


class TestImplementationDetails:
    def test_instance(self):
        assert issubclass(QDataModel, QtCore.QAbstractTableModel)

    def test_model_attributes(self):
        # test the actual implementation, not a mocked fixture
        qmodel = QDataModel()
        assert isinstance(qmodel._data, DataModel)


@pytest.fixture()
def qmodel(mocker: MockerFixture):
    model = QDataModel()
    mocker.patch.object(model, "_data")
    return model


class TestQtRequired:
    def test_rowCount(self, qmodel: QDataModel):
        assert qmodel.rowCount() == qmodel._data.num_rows.return_value

    def test_rowCount_valid_parent(self, qmodel: QDataModel):
        """Valid parent has no children in a table."""
        index = qmodel.createIndex(0, 0)
        assert qmodel.rowCount(index) == 0

    def test_columnCount(self, qmodel: QDataModel):
        assert qmodel.columnCount() == qmodel._data.num_columns.return_value

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
        qmodel._data.get_value.return_value = value
        qmodel._data.is_calculated_column.return_value = is_calculated

        if not role:
            actual = qmodel.data(index)
        else:
            actual = qmodel.data(index, role)

        qmodel._data.get_value.assert_called_once_with(row, column)
        assert actual == expected

    def test_data_returns_None_for_invalid_role(self, qmodel: QDataModel):
        index = qmodel.createIndex(2, 1)
        value = qmodel.data(index, QtCore.Qt.DecorationRole)
        assert value is None

    def test_headerData_for_columns(self, qmodel: QDataModel):
        actual = qmodel.headerData(sentinel.colidx, QtCore.Qt.Horizontal)

        qmodel._data.get_column_name.assert_called_once_with(sentinel.colidx)
        assert actual == qmodel._data.get_column_name.return_value

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

        qmodel._data.set_value.assert_called_once_with(1, 2, 3.0)
        qmodel.dataChanged.emit.assert_called_once_with(index, index)
        qmodel._data.recalculate_all_columns.assert_called()

    def test_setData_with_unsupported_role(self, qmodel: QDataModel):
        index = qmodel.createIndex(2, 1)
        retvalue = qmodel.setData(index, 5.0, QtCore.Qt.DecorationRole)
        assert retvalue is False

    @pytest.mark.parametrize("is_calculated", [True, False])
    def test_flags(self, qmodel: QDataModel, is_calculated):
        qmodel._data.is_calculated_column.return_value = is_calculated
        expected = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if not is_calculated:
            expected |= QtCore.Qt.ItemIsEditable

        index = qmodel.createIndex(2, 123)
        flags = qmodel.flags(index)

        qmodel._data.is_calculated_column.assert_called_once_with(123)
        assert flags == expected

    def test_insertRows(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "beginInsertRows")
        mocker.patch.object(qmodel, "endInsertRows")
        parent = QtCore.QModelIndex()
        retvalue1 = qmodel.insertRows(3, 4, parent=parent)

        qmodel._data.insert_rows.assert_called_once_with(3, 4)
        assert retvalue1 is True
        # four rows: 3 (first), 4, 5, 6 (last)
        qmodel.beginInsertRows.assert_called_with(parent, 3, 6)
        qmodel.endInsertRows.assert_called()
        qmodel._data.recalculate_all_columns.assert_called()

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

        qmodel._data.remove_rows.assert_called_once_with(3, 4)
        assert retvalue is True
        # four rows: 3 (first), 4, 5, 6 (last)
        qmodel.beginRemoveRows.assert_called_with(parent, 3, 6)
        qmodel.endRemoveRows.assert_called()
        qmodel._data.recalculate_all_columns.assert_called()

    def test_removeRows_valid_parent(self, qmodel: QDataModel):
        """You can't remove rows inside cells."""
        assert qmodel.removeRows(0, 2, parent=qmodel.createIndex(0, 0)) is False

    def test_removeRows_no_parent(self, qmodel: QDataModel):
        assert qmodel.removeRows(3, 4) is True

    def test_insertColumns(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "beginInsertColumns")
        mocker.patch.object(qmodel, "endInsertColumns")
        parent = QtCore.QModelIndex()
        retvalue = qmodel.insertColumns(3, 4, parent=parent)

        qmodel._data.insert_columns.assert_called_once_with(3, 4)
        assert retvalue is True
        # four columns: 3 (first), 4, 5, 6 (last)
        qmodel.beginInsertColumns.assert_called_with(parent, 3, 6)
        qmodel.endInsertColumns.assert_called()

    def test_insertColumns_no_parent(self, qmodel: QDataModel):
        assert qmodel.insertColumns(3, 4) is True

    def test_insertColumns_valid_parent(self, qmodel: QDataModel):
        """You can't add columns inside cells."""
        assert qmodel.insertColumns(0, 2, parent=qmodel.createIndex(0, 0)) is False

    def test_removeColumns(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "beginRemoveColumns")
        mocker.patch.object(qmodel, "endRemoveColumns")
        parent = QtCore.QModelIndex()
        retvalue = qmodel.removeColumns(3, 4, parent=parent)

        qmodel._data.remove_columns.assert_called_once_with(3, 4)
        assert retvalue is True
        # four columns: 3 (first), 4, 5, 6 (last)
        qmodel.beginRemoveColumns.assert_called_with(parent, 3, 6)
        qmodel.endRemoveColumns.assert_called()

    def test_removeColumns_valid_parent(self, qmodel: QDataModel):
        """You can't remove columns inside cells."""
        assert qmodel.removeColumns(0, 2, parent=qmodel.createIndex(0, 0)) is False

    def test_removeColumns_no_parent(self, qmodel: QDataModel):
        assert qmodel.removeColumns(3, 4) is True

    def test_moveColumn_right(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "beginMoveColumns")
        mocker.patch.object(qmodel, "endMoveColumns")
        parent = QtCore.QModelIndex()

        retvalue = qmodel.moveColumn(parent, 3, parent, 5)

        # pay attention to Qt conventions, see method docstring
        qmodel._data.move_column.assert_called_once_with(3, 5 - 1)
        assert retvalue is True
        qmodel.beginMoveColumns.assert_called_with(parent, 3, 3, parent, 5)
        qmodel.endMoveColumns.assert_called()

    def test_moveColumn_left(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "beginMoveColumns")
        mocker.patch.object(qmodel, "endMoveColumns")
        parent = QtCore.QModelIndex()
        retvalue = qmodel.moveColumn(parent, 5, parent, 3)

        # pay attention to Qt conventions, see method docstring
        qmodel._data.move_column.assert_called_once_with(5, 3)
        assert retvalue is True
        qmodel.beginMoveColumns.assert_called_with(parent, 5, 5, parent, 3)
        qmodel.endMoveColumns.assert_called()

    def test_moveColumn_invalid_move(self, qmodel: QDataModel):
        parent = QtCore.QModelIndex()

        retvalue = qmodel.moveColumn(parent, 3, parent, 4)

        assert retvalue is False

    def test_moveColumn_valid_parent(self, qmodel: QDataModel):
        """You can't move columns inside cells."""
        valid_parent = qmodel.createIndex(0, 0)
        invalid_parent = QtCore.QModelIndex()
        assert qmodel.moveColumn(valid_parent, 0, invalid_parent, 2) is False
        assert qmodel.moveColumn(invalid_parent, 0, valid_parent, 2) is False
        assert qmodel.moveColumn(valid_parent, 0, valid_parent, 2) is False

    def test_moveColumn_no_parents(self, qmodel: QDataModel):
        assert qmodel.moveColumn(sourceColumn=0, destinationChild=2) is True


class TestAPI:
    def test_insertCalculatedColumn(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "beginInsertColumns")
        mocker.patch.object(qmodel, "endInsertColumns")
        parent = QtCore.QModelIndex()
        retvalue = qmodel.insertCalculatedColumn(3, parent=parent)

        qmodel._data.insert_calculated_column.assert_called_once_with(3)
        assert retvalue is True
        qmodel.beginInsertColumns.assert_called_with(parent, 3, 3)
        qmodel.endInsertColumns.assert_called()

    def test_insertCalculatedColumn_no_parent(self, qmodel: QDataModel):
        assert qmodel.insertCalculatedColumn(3) is True

    def test_insertCalculatedColumn_valid_parent(self, qmodel: QDataModel):
        """You can't add columns inside cells."""
        assert (
            qmodel.insertCalculatedColumn(0, parent=qmodel.createIndex(0, 0)) is False
        )
