import sys

from tailor.data_sheet import DataSheet
from tailor.plot_tab import DrawCurve
from tailor.project_models import Parameter, Plot, Project, Sheet

DRAW_CURVE_OPTION_TABLE = [DrawCurve.ON_DATA, DrawCurve.ON_DOMAIN, DrawCurve.ON_AXIS]


def load_legacy_project(jsondict: dict) -> Project:
    sheet = get_sheet_from_project(jsondict)
    plots = get_plots_from_project(jsondict)
    project = Project(
        application=jsondict["application"],
        version=jsondict["version"],
        sheet_num=2,
        plot_num=len(plots) + 1,
        sheets=[sheet],
        plots=plots,
        multiplots=[],
        tab_order=["sheet_1"] + [f"plot_{plot.id}" for plot in plots],
        current_tab=jsondict["current_tab"],
    )
    return project


def get_sheet_from_project(jsondict: dict) -> Sheet:
    data = jsondict["data_model"]["data"]
    col_expressions = {
        k: v if v is not None else ""
        for k, v in jsondict["data_model"]["calculated_columns"].items()
    }
    return Sheet(
        name="Sheet 1",
        id=1,
        data=data,
        new_col_num=jsondict["data_model"]["new_col_num"],
        col_names={k: k for k in data.keys()},
        calculated_column_expression=col_expressions,
    )


def get_plots_from_project(jsondict: dict) -> list[Plot]:
    plots = []
    plot_id = 1
    for tab in jsondict["tabs"]:
        parameters = [
            Parameter(
                name=k, value=v["value"], min=v["min"], max=v["max"], vary=v["vary"]
            )
            for k, v in tab["parameters"].items()
        ]
        plots.append(
            Plot(
                name=tab["label"],
                data_sheet_id=1,
                id=plot_id,
                x_col=tab["x_var"],
                y_col=tab["y_var"],
                x_err_col=tab["x_err_var"],
                y_err_col=tab["y_err_var"],
                x_label=tab["xlabel"],
                y_label=tab["ylabel"],
                x_min=value if (value := tab["xmin"]) != "" else None,
                x_max=value if (value := tab["xmax"]) != "" else None,
                y_min=value if (value := tab["ymin"]) != "" else None,
                y_max=value if (value := tab["ymax"]) != "" else None,
                modelexpression=tab["model_func"],
                parameters=parameters,
                fit_domain=tab["fit_domain"],
                use_fit_domain=bool(tab["use_fit_domain"]),
                best_fit=bool(tab["saved_fit"]),
                show_initial_fit=tab["show_initial_fit"],
                draw_curve_option=DRAW_CURVE_OPTION_TABLE[tab["draw_curve_option"]],
            )
        )
        plot_id += 1
    return plots
