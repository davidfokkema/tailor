from unittest.mock import MagicMock, sentinel

import numpy as np
import pytest
from PySide6 import QtWidgets
from pytest_mock import MockerFixture

import tailor.data_sheet
from tailor.data_sheet import DataSheet

QtWidgets.QApplication()


@pytest.fixture()
def data_sheet(mocker: MockerFixture):
    main_window = mocker.Mock()
    return DataSheet(name="sheet1", id=1234, main_window=main_window)


@pytest.fixture()
def bare_bones_data_sheet(mocker: MockerFixture):
    mocker.patch.object(tailor.data_sheet, "Ui_DataSheet")
    mocker.patch.object(tailor.data_sheet, "QDataModel")
    mocker.patch.object(DataSheet, "connect_ui_events")
    mocker.patch.object(DataSheet, "setup_keyboard_shortcuts")
    mocker.patch.object(QtWidgets.QApplication, "clipboard")
    main_window = mocker.Mock()
    data_sheet = DataSheet(name="sheet1", id=1234, main_window=main_window)
    data_sheet.selection = mocker.Mock()
    return data_sheet


class TestDataSheet:
    def test_fixture_properties(self, bare_bones_data_sheet: DataSheet):
        assert isinstance(bare_bones_data_sheet, DataSheet)
        assert isinstance(bare_bones_data_sheet.ui, MagicMock)

    def test_init_sets_attributes(self, bare_bones_data_sheet: DataSheet):
        assert bare_bones_data_sheet.name == "sheet1"
        assert bare_bones_data_sheet.id == 1234

    def test_init_calls_setup(self, bare_bones_data_sheet: DataSheet):
        bare_bones_data_sheet.connect_ui_events.assert_called_once()
        bare_bones_data_sheet.setup_keyboard_shortcuts.assert_called_once()

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

    def test_copy_selected_cells(
        self, bare_bones_data_sheet: DataSheet, mocker: MockerFixture
    ):
        mocker.patch.object(bare_bones_data_sheet, "array_to_text")
        bare_bones_data_sheet.selection.selection.return_value = sentinel.selection
        bare_bones_data_sheet.data_model.dataFromSelection.return_value = sentinel.data
        bare_bones_data_sheet.array_to_text.return_value = sentinel.text

        bare_bones_data_sheet.copy_selected_cells()

        bare_bones_data_sheet.selection.selection.assert_called()
        bare_bones_data_sheet.data_model.dataFromSelection.assert_called_with(
            sentinel.selection
        )
        bare_bones_data_sheet.clipboard.setText.assert_called_with(sentinel.text)

    def test_paste_cells_sets_data(
        self, bare_bones_data_sheet: DataSheet, mocker: MockerFixture
    ):
        mocker.patch.object(bare_bones_data_sheet, "text_to_array")
        bare_bones_data_sheet.ui.data_view.currentIndex.return_value = sentinel.index
        bare_bones_data_sheet.clipboard.text.return_value = sentinel.text
        data = np.array([[1.0, 2.0]])
        bare_bones_data_sheet.text_to_array.return_value = data

        bare_bones_data_sheet.paste_cells()

        bare_bones_data_sheet.text_to_array.assert_called_with(sentinel.text)
        bare_bones_data_sheet.data_model.setDataFromArray.assert_called_with(
            sentinel.index, data
        )

    def test_array_to_text(self, bare_bones_data_sheet: DataSheet):
        data = np.array([[9.0, 10.0, np.nan], [15.0, 16.0, np.nan], [21.0, 22.0, 23.0]])
        expected = "9.0\t10.0\t\n15.0\t16.0\t\n21.0\t22.0\t23.0"

        assert bare_bones_data_sheet.array_to_text(data) == expected

    def test_text_to_array(self, bare_bones_data_sheet: DataSheet):
        data = "1.0\t\n3.0\t4.0\n5.0\t6.0"
        expected = np.array([[1.0, np.nan], [3.0, 4.0], [5.0, 6.0]])

        actual = bare_bones_data_sheet.text_to_array(data)

        assert actual.shape == expected.shape
        assert actual.flatten().tolist() == pytest.approx(
            expected.flatten().tolist(), nan_ok=True
        )

    def test_text_to_array_corrupt_data(self, bare_bones_data_sheet: DataSheet):
        data = "foobar"
        assert bare_bones_data_sheet.text_to_array(data) is None

    def test_text_to_array_no_data(self, bare_bones_data_sheet: DataSheet):
        data = ""
        assert bare_bones_data_sheet.text_to_array(data) is None


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
