from unittest.mock import call, sentinel

import numpy as np
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
        assert isinstance(qmodel.data_model, DataModel)


@pytest.fixture()
def qmodel(mocker: MockerFixture):
    model = QDataModel()
    mocker.patch.object(model, "data_model")
    return model


@pytest.fixture()
def calc_data():
    model = QDataModel()
    for _ in range(5):
        model.insertCalculatedColumn(0)
    model.insertRows(0, 10)
    return model


@pytest.fixture()
def data():
    model = QDataModel()
    model.insertColumns(0, 5)
    model.insertRows(0, 10)
    return model


class TestQtRequired:
    def test_rowCount(self, qmodel: QDataModel):
        assert qmodel.rowCount() == qmodel.data_model.num_rows.return_value

    def test_rowCount_valid_parent(self, qmodel: QDataModel):
        """Valid parent has no children in a table."""
        index = qmodel.createIndex(0, 0)
        assert qmodel.rowCount(index) == 0

    def test_columnCount(self, qmodel: QDataModel):
        assert qmodel.columnCount() == qmodel.data_model.num_columns.return_value

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
        qmodel.data_model.get_value.return_value = value
        qmodel.data_model.is_calculated_column.return_value = is_calculated

        if not role:
            actual = qmodel.data(index)
        else:
            actual = qmodel.data(index, role)

        qmodel.data_model.get_value.assert_called_once_with(row, column)
        assert actual == expected

    def test_data_returns_None_for_invalid_role(self, qmodel: QDataModel):
        index = qmodel.createIndex(2, 1)
        value = qmodel.data(index, QtCore.Qt.DecorationRole)
        assert value is None

    @pytest.mark.parametrize("role", [QtCore.Qt.DisplayRole, QtCore.Qt.BackgroundRole])
    def test_data_uses_column_label(self, qmodel: QDataModel, role):
        index = qmodel.createIndex(2, 1)
        qmodel.data_model.get_value.return_value = np.nan
        qmodel.data_model.get_column_label.return_value = sentinel.label

        qmodel.data(index, role)

        qmodel.data_model.is_calculated_column.assert_called_with(sentinel.label)
        if role == QtCore.Qt.BackgroundRole:
            qmodel.data_model.is_column_valid.assert_called_with(sentinel.label)

    def test_headerData_for_columns(self, qmodel: QDataModel):
        qmodel.data_model.get_column_label.return_value = sentinel.label

        actual = qmodel.headerData(sentinel.colidx, QtCore.Qt.Horizontal)

        qmodel.data_model.get_column_label.assert_called_once_with(sentinel.colidx)
        qmodel.data_model.get_column_name.assert_called_once_with(sentinel.label)
        assert actual == qmodel.data_model.get_column_name.return_value

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
        index = qmodel.createIndex(1, 2)

        if role:
            qmodel.setData(index, 3, role)
        else:
            qmodel.setData(index, 3)

        qmodel.data_model.set_value.assert_called_once_with(1, 2, 3.0)

    def test_setData_with_unsupported_role(self, qmodel: QDataModel):
        index = qmodel.createIndex(2, 1)
        retvalue = qmodel.setData(index, 5.0, QtCore.Qt.DecorationRole)
        assert retvalue is False

    @pytest.mark.parametrize("is_calculated", [True, False])
    def test_flags(self, qmodel: QDataModel, is_calculated):
        qmodel.data_model.get_column_label.return_value = sentinel.label
        qmodel.data_model.is_calculated_column.return_value = is_calculated
        expected = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if not is_calculated:
            expected |= QtCore.Qt.ItemIsEditable

        index = qmodel.createIndex(2, 123)
        flags = qmodel.flags(index)

        qmodel.data_model.get_column_label.assert_called_with(123)
        qmodel.data_model.is_calculated_column.assert_called_once_with(sentinel.label)
        assert flags == expected

    def test_insertRows(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "beginInsertRows")
        mocker.patch.object(qmodel, "endInsertRows")
        parent = QtCore.QModelIndex()
        retvalue1 = qmodel.insertRows(3, 4, parent=parent)

        qmodel.data_model.insert_rows.assert_called_once_with(3, 4)
        assert retvalue1 is True
        # four rows: 3 (first), 4, 5, 6 (last)
        qmodel.beginInsertRows.assert_called_with(parent, 3, 6)
        qmodel.endInsertRows.assert_called()

    def test_insertRows_valid_parent(self, qmodel: QDataModel):
        """You can't add rows inside cells."""
        assert qmodel.insertRows(0, 2, parent=qmodel.createIndex(0, 0)) is False

    def test_insertRows_no_parent(self, qmodel: QDataModel):
        assert qmodel.insertRows(3, 4) is True

    def test_insertRows_no_columns(self, qmodel: QDataModel):
        qmodel.data_model.num_columns.return_value = 0

        assert qmodel.insertRows(0, 10) is False

    def test_removeRows(self, qmodel: QDataModel, mocker: MockerFixture):
        # WIP: test that begin/endRemoveRows is called
        mocker.patch.object(qmodel, "beginRemoveRows")
        mocker.patch.object(qmodel, "endRemoveRows")
        parent = QtCore.QModelIndex()
        retvalue = qmodel.removeRows(3, 4, parent=parent)

        qmodel.data_model.remove_rows.assert_called_once_with(3, 4)
        assert retvalue is True
        # four rows: 3 (first), 4, 5, 6 (last)
        qmodel.beginRemoveRows.assert_called_with(parent, 3, 6)
        qmodel.endRemoveRows.assert_called()

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

        qmodel.data_model.insert_columns.assert_called_once_with(3, 4)
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

        qmodel.data_model.remove_columns.assert_called_once_with(3, 4)
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
        qmodel.data_model.get_column_label.return_value = sentinel.label
        parent = QtCore.QModelIndex()

        retvalue = qmodel.moveColumn(parent, 3, parent, 5)

        # pay attention to Qt conventions, see method docstring
        qmodel.data_model.move_column.assert_called_once_with(3, 5 - 1)
        assert retvalue is True
        qmodel.beginMoveColumns.assert_called_with(parent, 3, 3, parent, 5)
        qmodel.endMoveColumns.assert_called()

    def test_moveColumn_left(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "beginMoveColumns")
        mocker.patch.object(qmodel, "endMoveColumns")
        qmodel.data_model.get_column_label.return_value = sentinel.label
        parent = QtCore.QModelIndex()

        retvalue = qmodel.moveColumn(parent, 5, parent, 3)

        # pay attention to Qt conventions, see method docstring
        qmodel.data_model.move_column.assert_called_once_with(5, 3)
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

        qmodel.data_model.insert_calculated_column.assert_called_once_with(3)
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

    def test_columnLabel(self, qmodel: QDataModel):
        qmodel.data_model.get_column_label.return_value = sentinel.label

        name = qmodel.columnLabel(sentinel.idx)

        qmodel.data_model.get_column_label.assert_called_with(sentinel.idx)
        assert name == sentinel.label

    def test_columnLabels(self, qmodel: QDataModel):
        qmodel.data_model.get_column_labels.return_value = sentinel.labels

        assert qmodel.columnLabels() == sentinel.labels

    def test_columnName(self, qmodel: QDataModel):
        qmodel.data_model.get_column_label.return_value = sentinel.label
        qmodel.data_model.get_column_name.return_value = sentinel.name

        name = qmodel.columnName(sentinel.idx)

        qmodel.data_model.get_column_label.assert_called_with(sentinel.idx)
        qmodel.data_model.get_column_name.assert_called_with(sentinel.label)
        assert name == sentinel.name

    def test_columnNames(self, qmodel: QDataModel):
        qmodel.data_model.get_column_names.return_value = sentinel.names

        assert qmodel.columnNames() == sentinel.names

    def test_renameColumn(self, qmodel: QDataModel):
        qmodel.data_model.get_column_label.return_value = sentinel.label
        qmodel.data_model.rename_column.return_value = sentinel.new_name

        new_name = qmodel.renameColumn(sentinel.idx, sentinel.name)

        qmodel.data_model.get_column_label.assert_called_with(sentinel.idx)
        qmodel.data_model.rename_column.assert_called_with(
            sentinel.label, sentinel.name
        )
        assert new_name == sentinel.new_name

    def test_isCalculatedColumn(self, qmodel: QDataModel):
        qmodel.data_model.get_column_label.return_value = sentinel.label
        qmodel.data_model.is_calculated_column.return_value = sentinel.is_calculated

        actual = qmodel.isCalculatedColumn(sentinel.idx)

        qmodel.data_model.get_column_label.assert_called_with(sentinel.idx)
        qmodel.data_model.is_calculated_column.assert_called_with(sentinel.label)
        assert actual == sentinel.is_calculated

    def test_columnExpression(self, qmodel: QDataModel):
        qmodel.data_model.get_column_label.return_value = sentinel.label
        qmodel.data_model.get_column_expression.return_value = sentinel.expression

        expression = qmodel.columnExpression(sentinel.idx)

        qmodel.data_model.get_column_label.assert_called_with(sentinel.idx)
        qmodel.data_model.get_column_expression.assert_called_with(sentinel.label)
        assert expression == sentinel.expression

    def test_updateColumnExpression(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "createIndex")
        mocker.patch.object(qmodel, "dataChanged")
        qmodel.data_model.get_column_label.return_value = sentinel.label

        success = qmodel.updateColumnExpression(sentinel.idx, sentinel.expr)

        assert success is True
        qmodel.data_model.get_column_label.assert_called_with(sentinel.idx)
        qmodel.data_model.update_column_expression.assert_called_with(
            sentinel.label, sentinel.expr
        )

    def test_updateColumnExpression_returns_false(
        self, qmodel: QDataModel, mocker: MockerFixture
    ):
        mocker.patch.object(qmodel, "isCalculatedColumn").return_value = False
        print(qmodel.isCalculatedColumn(0))
        assert qmodel.updateColumnExpression(0, "Foo") is False

    def test_updateColumnExpression_emits_dataChanged(
        self, calc_data: QDataModel, mocker: MockerFixture
    ):
        mocker.patch.object(calc_data, "dataChanged")
        top_left = calc_data.createIndex(0, 2)
        bottom_right = calc_data.createIndex(9, 4)

        calc_data.updateColumnExpression(2, "x ** 2")

        calc_data.dataChanged.emit.assert_called_with(top_left, bottom_right)

    def test_clearData(self, qmodel: QDataModel):
        selection = QtCore.QItemSelection(
            qmodel.createIndex(0, 1), qmodel.createIndex(1, 1)
        )

        qmodel.clearData(selection)

        qmodel.data_model.set_values.assert_called_with(0, 1, 1, 1, np.nan)

    def test_clearData_with_multiple_selections(self, qmodel: QDataModel):
        selection = QtCore.QItemSelection(
            qmodel.createIndex(0, 1), qmodel.createIndex(1, 1)
        )
        selection.append(
            QtCore.QItemSelection(qmodel.createIndex(2, 2), qmodel.createIndex(2, 2))
        )

        qmodel.clearData(selection)

        expected = [call(0, 1, 1, 1, np.nan), call(2, 2, 2, 2, np.nan)]
        assert qmodel.data_model.set_values.call_args_list == expected

    def test_clearData_calls_dataChanged(
        self, qmodel: QDataModel, mocker: MockerFixture
    ):
        mocker.patch.object(qmodel, "dataChanged")
        mocker.patch.object(qmodel, "columnCount")
        qmodel.columnCount.return_value = 10
        topleft1 = qmodel.createIndex(0, 1)
        bottomright1 = qmodel.createIndex(2, 3)
        bottomfarright1 = qmodel.createIndex(2, 10 - 1)
        topleft2 = qmodel.createIndex(4, 5)
        bottomright2 = qmodel.createIndex(6, 7)
        bottomfarright2 = qmodel.createIndex(6, 10 - 1)

        selection = QtCore.QItemSelection(topleft1, bottomright1)
        selection.append(QtCore.QItemSelection(topleft2, bottomright2))

        qmodel.clearData(selection)

        expected = [call(topleft1, bottomfarright1), call(topleft2, bottomfarright2)]
        assert qmodel.dataChanged.emit.call_args_list == expected

    def test_dataFromSelection(self, qmodel: QDataModel, mocker: MockerFixture):
        """Test copying data from a selection.

        Given the data and selection:

             1  2  3  4  5  6
                 ┌─────┐
             7  8│ 9 10│11 12
                 │     │
            13 14│15 16│17 18
                 │     ├──┐
            19 20│21 22│23│24
                 └─────┴──┘
            25 26 27 28 29 30

        The result should be:

             9 10 NaN

            15 16 NaN

            21 22 223
        """
        qmodel.data_model.get_values.side_effect = (
            np.array([[9.0, 10.0], [15.0, 16.0], [21.0, 22.0]]),
            np.array([[23.0]]),
        )
        selection = QtCore.QItemSelection(
            qmodel.createIndex(1, 2), qmodel.createIndex(3, 3)
        )
        selection.append(
            QtCore.QItemSelection(qmodel.createIndex(3, 4), qmodel.createIndex(3, 4))
        )

        values = qmodel.dataFromSelection(selection)

        assert qmodel.data_model.get_values.call_args_list == [
            call(1, 2, 3, 3),
            call(3, 4, 3, 4),
        ]
        assert values.shape == (3, 3)
        assert values.flatten().tolist() == pytest.approx(
            [9.0, 10.0, np.nan, 15.0, 16.0, np.nan, 21.0, 22.0, 23.0], nan_ok=True
        )

    def test_setDataFromArray(self, qmodel: QDataModel, mocker: MockerFixture):
        mocker.patch.object(qmodel, "rowCount")
        mocker.patch.object(qmodel, "columnCount")
        mocker.patch.object(qmodel, "insertRows")
        mocker.patch.object(qmodel, "insertColumns")
        qmodel.rowCount.return_value = 5
        qmodel.columnCount.return_value = 3
        values = np.zeros(shape=(7, 8))
        index = qmodel.createIndex(1, 2)

        qmodel.setDataFromArray(index, values)

        # (7 + 1) - 5 = 3 rows too short
        # (8 + 2) - 3 = 7 columns too short
        qmodel.insertRows.assert_called_with(5, 3)
        qmodel.insertColumns.assert_called_with(3, 7)
        qmodel.data_model.set_values_from_array.assert_called_with(1, 2, values)

    def test_setDataFromArray_emits_dataChanged(
        self, data: QDataModel, mocker: MockerFixture
    ):
        mocker.patch.object(data, "dataChanged")
        index = data.createIndex(1, 2)
        values = np.zeros(shape=(4, 1))
        # all columns to the right may have changed (updated calculations)
        # 'data' object has 5 columns, so last column has index 4
        bottomfarright = data.createIndex(1 + 4 - 1, 4)

        data.setDataFromArray(index, values)

        data.dataChanged.emit.assert_called_with(index, bottomfarright)
