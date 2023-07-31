import lmfit
import numpy as np
import pytest
from pytest_mock import MockerFixture, mocker

import tailor.data_sheet
from tailor import plot_model, project_files
from tailor.app import Application
from tailor.data_sheet import DataSheet
from tailor.plot_tab import PlotTab


@pytest.fixture()
def data_sheet(mocker: MockerFixture) -> DataSheet:
    sheet = DataSheet(name="sheet1", id=1234, main_window=mocker.MagicMock())
    sheet.data_model.setDataFromArray(
        sheet.data_model.createIndex(0, 0),
        np.array(
            [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [float("nan"), 1.0, 4.0, 9.0, 16.0, 25.0]]
        ).T,
    )
    sheet.data_model.insertCalculatedColumn(2)
    sheet.data_model.insertCalculatedColumn(3)
    sheet.data_model.insertCalculatedColumn(4)
    sheet.data_model.renameColumn(0, "x")
    sheet.data_model.renameColumn(1, "y")
    sheet.data_model.renameColumn(2, "z")
    sheet.data_model.renameColumn(3, "yerr")
    sheet.data_model.updateColumnExpression(2, "0.02 * x ** 2")
    sheet.data_model.updateColumnExpression(3, "0.1")
    return sheet


@pytest.fixture()
def data_sheet_model(data_sheet) -> project_files.Sheet:
    return project_files.save_data_sheet(data_sheet)


@pytest.fixture()
def plot_tab(data_sheet: DataSheet, mocker: MockerFixture) -> PlotTab:
    plot_tab = PlotTab(
        name="Plot 1",
        data_sheet=data_sheet,
        x_col="col1",
        y_col="col2",
        x_err_col="col3",
        y_err_col="col4",
    )
    plot_tab.model.update_model_expression("a * x + b")
    plot_tab.model.x_label = "Time"
    plot_tab.model.y_label = "Distance"
    plot_tab.model.perform_fit()
    return plot_tab


@pytest.fixture()
def plot_tab_model(plot_tab) -> project_files.Plot:
    return project_files.save_plot(plot_tab)


@pytest.fixture()
def simple_project(data_sheet: DataSheet, plot_tab: PlotTab) -> Application:
    app = Application()
    app.ui.tabWidget.removeTab(0)
    app.ui.tabWidget.addTab(data_sheet, data_sheet.name)
    app.ui.tabWidget.addTab(plot_tab, plot_tab.name)
    app.ui.tabWidget.setCurrentIndex(1)
    return app


@pytest.fixture()
def simple_project_model(simple_project: Application) -> project_files.Project:
    return project_files.save_project_to_model(simple_project)


class TestProjectFiles:
    def test_save_data_sheet(self, data_sheet: DataSheet):
        sheet = project_files.save_data_sheet(data_sheet)
        assert sheet.name == "sheet1"
        assert sheet.id == 1234
        assert sheet.col_names == {
            "col1": "x",
            "col2": "y",
            "col3": "z",
            "col4": "yerr",
        }
        assert sheet.data["col1"] == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        assert sheet.data["col2"] == pytest.approx(
            [float("nan"), 1.0, 4.0, 9.0, 16.0, 25.0], nan_ok=True
        )
        assert sheet.data["col3"] == [0.0, 0.02, 0.08, 0.18, 0.32, 0.50]
        assert sheet.data["col4"] == 6 * [0.1]
        assert sheet.new_col_num == 4
        assert sheet.calculated_column_expression["col3"] == "0.02 * col1 ** 2"
        assert sheet.calculated_column_expression["col4"] == "0.1"
        assert sheet.is_calculated_column_valid["col3"] is True
        assert sheet.is_calculated_column_valid["col4"] is True

    def test_load_data_sheet(
        self, data_sheet_model: project_files.Sheet, mocker: MockerFixture
    ):
        app = mocker.Mock()
        mocker.patch.object(project_files.DataSheet, "selection_changed")
        mocker.patch.object(tailor.data_sheet.QDataModel, "beginResetModel")
        mocker.patch.object(tailor.data_sheet.QDataModel, "endResetModel")
        data_sheet = project_files.load_data_sheet(app, data_sheet_model)
        assert isinstance(data_sheet, DataSheet)
        assert data_sheet.data_model.rowCount() == 6
        # test single value
        assert (
            data_sheet.data_model.data(data_sheet.data_model.createIndex(5, 1)) == "25"
        )
        assert data_sheet.data_model.columnExpression(2) == "0.02 * x ** 2"
        assert data_sheet.data_model.columnNames() == ["x", "y", "z", "yerr"]
        # must be called twice (once implicitly, once explicitly by our code)
        assert data_sheet.selection_changed.call_count == 2
        # begin/end reset model _must_ be called otherwise shape of data will be
        # the default shape of two columns, five rows.
        data_sheet.data_model.beginResetModel.assert_called()
        data_sheet.data_model.endResetModel.assert_called()

    def test_save_plot(self, plot_tab: PlotTab):
        plot = project_files.save_plot(plot_tab)
        assert plot.name == "Plot 1"
        assert plot.data_sheet_id == 1234
        assert plot.x_col == "col1"
        assert plot.y_col == "col2"
        assert plot.x_err_col == "col3"
        assert plot.y_err_col == "col4"
        assert plot.x_label == "Time"
        assert plot.y_label == "Distance"
        assert plot.modelexpression == "a * col1 + b"
        param_names = [p.name for p in plot.parameters]
        assert "a" in param_names
        assert "b" in param_names

    def test_load_plot(
        self,
        plot_tab_model: project_files.Plot,
        data_sheet: DataSheet,
        mocker: MockerFixture,
    ):
        app = mocker.Mock()
        plot_tab = project_files.load_plot(app, plot_tab_model, data_sheet)
        assert isinstance(plot_tab, PlotTab)

        assert plot_tab.name == "Plot 1"
        assert isinstance(plot_tab.data_sheet, DataSheet)
        assert plot_tab.model.x_col == "col1"
        assert plot_tab.model.y_col == "col2"
        assert plot_tab.model.x_err_col == "col3"
        assert plot_tab.model.y_err_col == "col4"
        assert plot_tab.model.x_label == "Time"
        assert plot_tab.model.y_label == "Distance"
        assert plot_tab.model.model_expression == "a * col1 + b"
        param_names = plot_tab.model.parameters.keys()
        assert "a" in param_names
        assert "b" in param_names
        assert isinstance(plot_tab.model.parameters["a"], plot_model.Parameter)
        assert isinstance(plot_tab.model.best_fit, lmfit.model.ModelResult)

    def test_load_project_from_model(self, simple_project_model: project_files.Project):
        app = Application()
        project_files.load_project_from_model(app, simple_project_model)

        sheet = app.ui.tabWidget.widget(0)
        plot = app.ui.tabWidget.widget(1)
        assert isinstance(sheet, DataSheet)
        assert isinstance(plot, PlotTab)
        assert plot.data_sheet is sheet
        assert app.ui.tabWidget.currentIndex() == simple_project_model.current_tab

    def test_save_project_to_json_completes(self, simple_project: Application):
        project_files.save_project_to_json(simple_project)

    def test_load_project_from_json(self, simple_project: Application):
        json = project_files.save_project_to_json(simple_project)
        project = Application()
        project_files.load_project_from_json(project, json)
        assert project.ui.tabWidget.count() == 2

    def test_save_project_to_path(self, simple_project: Application, tmp_path):
        project_files.save_project_to_path(simple_project, tmp_path / "project.tlr")

    def test_open_project_from_path(self, simple_project: Application, tmp_path):
        project_files.save_project_to_path(simple_project, tmp_path / "project.tlr")
        app = Application()

        project_files.load_project_from_path(app, tmp_path / "project.tlr")

        assert app.ui.tabWidget.count() == 2
        assert isinstance(app.ui.tabWidget.widget(0), DataSheet)
        assert isinstance(app.ui.tabWidget.widget(1), PlotTab)
