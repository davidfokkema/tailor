from __future__ import annotations

import gzip
import importlib.metadata
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from packaging.version import Version

from tailor import plot_model
from tailor.data_sheet import DataSheet
from tailor.legacy_project_files import load_legacy_project
from tailor.plot_tab import PlotTab
from tailor.project_models import Parameter, Plot, Project, Sheet

if TYPE_CHECKING:
    from tailor.app import Application

metadata = importlib.metadata.metadata("tailor")
NAME = metadata["name"]
VERSION = metadata["version"]


def save_project_to_path(project: Application, path: Path) -> None:
    with gzip.open(path, mode="wt", encoding="utf-8") as f:
        f.write(save_project_to_json(project))


def load_project_from_path(project: Application, path: Path) -> None:
    with gzip.open(path, mode="rt", encoding="utf-8") as f:
        load_project_from_json(project, f.read())


def save_project_to_json(project: Application) -> str:
    model = save_project_to_model(project)
    return json.dumps(model.model_dump(), indent=4)


def load_project_from_json(project: Application, jsondata: str) -> None:
    jsondict = json.loads(jsondata)
    if jsondict["application"] == "tailor":
        file_version = Version(jsondict["version"])
        if Version(file_version.base_version) < Version("2.0"):
            model = load_legacy_project(jsondict)
        else:
            model = Project.model_validate(jsondict)
        load_project_from_model(project, model)


def save_project_to_model(project: Application):
    tabs = [
        project.ui.tabWidget.widget(idx) for idx in range(project.ui.tabWidget.count())
    ]
    sheet_models = []
    plot_models = []
    tab_order = []
    for tab in tabs:
        if isinstance(tab, DataSheet):
            sheet = save_data_sheet(tab)
            sheet_models.append(sheet)
            tab_order.append(f"sheet_{sheet.id}")
        elif isinstance(tab, PlotTab):
            plot = save_plot(tab)
            plot_models.append(plot)
            tab_order.append(f"plot_{plot.id}")

    model = Project(
        application=NAME,
        version=VERSION,
        sheet_num=project._sheet_num,
        plot_num=project._plot_num,
        sheets=sheet_models,
        plots=plot_models,
        tab_order=tab_order,
        current_tab=project.ui.tabWidget.currentIndex(),
    )

    return model


def load_project_from_model(project: Application, model: Project):
    # load all data sheets for reference
    data_sheet_by_id: dict[str, DataSheet] = {}
    for sheet_model in model.sheets:
        sheet = load_data_sheet(project, sheet_model)
        data_sheet_by_id[sheet.id] = sheet

    # load plots and add tabs to app
    plot_tab_by_id: dict[str, PlotTab] = {}
    for plot_model in model.plots:
        sheet = data_sheet_by_id[plot_model.data_sheet_id]
        plot_tab = load_plot(app=project, model=plot_model, data_sheet=sheet)
        plot_tab_by_id[plot_tab.id] = plot_tab

    # restore tabs in order
    for id_string in model.tab_order:
        type_, id = id_string.split("_")
        id = int(id)
        if type_ == "sheet":
            tab = data_sheet_by_id[id]
        elif type_ == "plot":
            tab = plot_tab_by_id[id]
        project.ui.tabWidget.addTab(tab, tab.name)
    project.ui.tabWidget.setCurrentIndex(model.current_tab)


def save_data_sheet(data_sheet: DataSheet) -> Sheet:
    data_model = data_sheet.data_model._data
    return Sheet(
        name=data_sheet.name,
        id=data_sheet.id,
        data=data_model._data.to_dict(orient="list"),
        new_col_num=data_model._new_col_num,
        col_names=data_model._col_names,
        calculated_column_expression=data_model._calculated_column_expression,
    )


def load_data_sheet(app: Application, model: Sheet) -> DataSheet:
    data_sheet = DataSheet(name=model.name, id=model.id, main_window=app)
    data_sheet.data_model.beginResetModel()
    data = data_sheet.data_model._data
    data._data = pd.DataFrame.from_dict(model.data)
    data._new_col_num = model.new_col_num
    data._col_names = model.col_names
    data._calculated_column_expression = model.calculated_column_expression
    data_sheet.data_model._data.recalculate_all_columns()
    data_sheet.data_model.endResetModel()
    # force updating column information in UI
    data_sheet.selection_changed()
    return data_sheet


def save_plot(plot: PlotTab):
    parameters = [
        Parameter(name=p.name, value=p.value, min=p.min, max=p.max, vary=p.vary)
        for p in plot.model.parameters.values()
    ]
    best_fit = plot.model.best_fit is not None
    return Plot(
        name=plot.name,
        id=plot.id,
        data_sheet_id=plot.data_sheet.id,
        x_col=plot.model.x_col,
        y_col=plot.model.y_col,
        x_err_col=plot.model.x_err_col,
        y_err_col=plot.model.y_err_col,
        x_label=plot.model.x_label,
        y_label=plot.model.y_label,
        x_min=plot.model.x_min,
        x_max=plot.model.x_max,
        y_min=plot.model.y_min,
        y_max=plot.model.y_max,
        modelexpression=plot.model.model_expression,
        parameters=parameters,
        fit_domain=plot.model.fit_domain,
        use_fit_domain=plot.model.use_fit_domain,
        best_fit=best_fit,
    )


def load_plot(app: Application, model: Plot, data_sheet: DataSheet) -> PlotTab:
    plot_tab = PlotTab(
        name=model.name,
        id=model.id,
        data_sheet=data_sheet,
        x_col=model.x_col,
        y_col=model.y_col,
        x_err_col=model.x_err_col,
        y_err_col=model.y_err_col,
    )
    plot_tab.model.x_label = model.x_label
    plot_tab.model.y_label = model.y_label
    plot_tab.model.x_min = model.x_min
    plot_tab.model.x_max = model.x_max
    plot_tab.model.y_min = model.y_min
    plot_tab.model.y_max = model.y_max
    plot_tab.model.update_model_expression(model.modelexpression)
    for parameter in model.parameters:
        plot_tab.model.parameters[parameter.name] = plot_model.Parameter(
            **parameter.model_dump()
        )
    plot_tab.model.fit_domain = model.fit_domain
    plot_tab.model.use_fit_domain = model.use_fit_domain
    if model.best_fit:
        plot_tab.model.perform_fit()
    return plot_tab
