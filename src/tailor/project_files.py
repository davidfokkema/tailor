import importlib
import json

import pandas as pd
from pydantic import BaseModel

from tailor import plot_model
from tailor.app import Application
from tailor.data_sheet import DataSheet
from tailor.plot_tab import PlotTab

metadata = importlib.metadata.metadata("tailor")
NAME = metadata["name"]
VERSION = metadata["version"]


class Sheet(BaseModel):
    name: str
    id: int
    data: dict[str, list]
    new_col_num: int
    col_names: dict[str, str]
    calculated_column_expression: dict[str, str]
    is_calculated_column_valid: dict[str, bool]


class Parameter(BaseModel):
    name: str
    value: float
    min: float
    max: float
    vary: bool


class Plot(BaseModel):
    name: str
    data_sheet_id: int

    x_col: str
    y_col: str
    x_err_col: str | None
    y_err_col: str | None

    x_label: str
    y_label: str

    x_min: float | None
    x_max: float | None
    y_min: float | None
    y_max: float | None

    modelexpression: str
    parameters: list[Parameter]
    fit_domain: tuple[float, float] | None
    use_fit_domain: bool
    best_fit: bool


class Project(BaseModel):
    application: str
    version: str
    sheet_num: int
    plot_num: int
    tabs: list[Sheet | Plot]
    current_tab: int


def save_project_to_json(project: Application) -> str:
    tabs = [
        project.ui.tabWidget.widget(idx) for idx in range(project.ui.tabWidget.count())
    ]
    tab_models = []
    for tab in tabs:
        if isinstance(tab, DataSheet):
            tab_models.append(save_data_sheet(tab))
        elif isinstance(tab, PlotTab):
            tab_models.append(save_plot(tab))

    model = Project(
        application=NAME,
        version=VERSION,
        sheet_num=project._sheet_num,
        plot_num=project._plot_num,
        tabs=tab_models,
        current_tab=project.ui.tabWidget.currentIndex(),
    )
    return json.dumps(model.model_dump(), indent=4)


def load_project_from_json(jsondata) -> Application:
    model = Project.model_validate(json.loads(jsondata))
    app = Application(add_sheet=False)
    data_sheet_by_id: dict[str, DataSheet] = {}
    # load all data sheets
    for tab in model.tabs:
        if isinstance(tab, Sheet):
            sheet = load_data_sheet(app, tab)
            data_sheet_by_id[sheet.id] = sheet
    for tab in model.tabs:
        if isinstance(tab, Sheet):
            sheet = data_sheet_by_id[tab.id]
            app.ui.tabWidget.addTab(sheet, sheet.name)
        elif isinstance(tab, Plot):
            sheet = data_sheet_by_id[tab.data_sheet_id]
            plot_tab = load_plot(app=app, model=tab, data_sheet=sheet)
            app.ui.tabWidget.addTab(plot_tab, plot_tab.name)
    return app


def save_data_sheet(data_sheet: DataSheet) -> Sheet:
    data_model = data_sheet.data_model._data
    return Sheet(
        name=data_sheet.name,
        id=data_sheet.id,
        data=data_model._data.to_dict(orient="list"),
        new_col_num=data_model._new_col_num,
        col_names=data_model._col_names,
        calculated_column_expression=data_model._calculated_column_expression,
        is_calculated_column_valid=data_model._is_calculated_column_valid,
    )


def load_data_sheet(app: Application, model: Sheet) -> DataSheet:
    data_sheet = DataSheet(name=model.name, id=model.id, main_window=app)
    data_model = data_sheet.data_model._data
    data_model._data = pd.DataFrame.from_dict(model.data)
    data_model._new_col_num = model.new_col_num
    data_model._col_names = model.col_names
    data_model._calculated_column_expression = model.calculated_column_expression
    data_model._is_calculated_column_valid = model.is_calculated_column_valid
    return data_sheet


def save_plot(plot: PlotTab):
    parameters = [
        Parameter(name=p.name, value=p.value, min=p.min, max=p.max, vary=p.vary)
        for p in plot.model.parameters.values()
    ]
    best_fit = plot.model.best_fit is not None
    return Plot(
        name=plot.name,
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
