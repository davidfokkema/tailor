from unittest.mock import MagicMock, sentinel

import pytest
from PySide6 import QtWidgets
from pytest_mock import MockerFixture

import tailor.data_sheet
from tailor.data_sheet import DataSheet

QtWidgets.QApplication()


@pytest.fixture()
def data_sheet(mocker: MockerFixture):
    main_window = mocker.Mock()
    return DataSheet("sheet1", main_window)


@pytest.fixture()
def bare_bones_data_sheet(mocker: MockerFixture):
    mocker.patch.object(tailor.data_sheet, "Ui_DataSheet")
    mocker.patch.object(tailor.data_sheet, "QDataModel")
    mocker.patch.object(DataSheet, "connect_ui_events")
    mocker.patch.object(DataSheet, "setup_keyboard_shortcuts")
    main_window = mocker.Mock()
    return DataSheet("sheet1", main_window)


class TestDataSheet:
    def test_fixture_properties(self, bare_bones_data_sheet: DataSheet):
        assert isinstance(bare_bones_data_sheet, DataSheet)
        assert isinstance(bare_bones_data_sheet.ui, MagicMock)
        DataSheet.connect_ui_events.assert_called_once()
        DataSheet.setup_keyboard_shortcuts.assert_called_once()

    def test_add_column(self, bare_bones_data_sheet: DataSheet):
        bare_bones_data_sheet.data_model.columnCount.return_value = sentinel.num_columns
        bare_bones_data_sheet.add_column()
        bare_bones_data_sheet.data_model.insertColumn.assert_called_once_with(
            sentinel.num_columns
        )

    def test_add_calculated_column(self, bare_bones_data_sheet: DataSheet):
        bare_bones_data_sheet.data_model.columnCount.return_value = sentinel.num_columns
        bare_bones_data_sheet.add_calculated_column()
        bare_bones_data_sheet.data_model.insertCalculatedColumn.assert_called_once_with(
            sentinel.num_columns
        )

    def test_selection_changed_uses_full_selection(
        self, bare_bones_data_sheet: DataSheet, mocker: MockerFixture
    ):
        bare_bones_data_sheet.selection = mocker.Mock()
        bare_bones_data_sheet.selection_changed(sentinel.new, sentinel.old)
        bare_bones_data_sheet.selection.selection.assert_called()


class TestIntegratedDataSheet:
    def test_fixture_properties(self, data_sheet: DataSheet):
        assert isinstance(data_sheet, DataSheet)
        assert data_sheet.data_model.columnCount() == 2
        assert data_sheet.data_model.rowCount() == 5

    def test_add_column(self, data_sheet: DataSheet):
        data_sheet.add_column()
        assert data_sheet.data_model.columnCount() == 3

    def test_add_calculated_column(self, data_sheet: DataSheet):
        data_sheet.add_calculated_column()
        assert data_sheet.data_model.columnCount() == 3
