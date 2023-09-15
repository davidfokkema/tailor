import sys

from tailor.data_sheet import DataSheet
from tailor.project_models import Parameter, Plot, Project, Sheet


def load_legacy_project(jsondict: dict) -> Project:
    try:
        sheet = get_sheet_from_project(jsondict)
        plots = get_plots_from_project(jsondict)
        project = Project(
            application=jsondict["application"],
            version=jsondict["version"],
            sheet_num=2,
            plot_num=len(plots) + 1,
            tabs=[sheet, *plots],
            current_tab=jsondict["current_tab"],
        )
        return project
    except Exception as exc:
        print(exc)
        sys.exit()


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
                x_col=tab["x_var"],
                y_col=tab["y_var"],
                x_err_col=tab["x_err_var"],
                y_err_col=tab["y_err_var"],
                x_label=tab["xlabel"],
                y_label=tab["ylabel"],
                x_min=tab["xmin"],
                x_max=tab["xmax"],
                y_min=tab["ymin"],
                y_max=tab["ymax"],
                modelexpression=tab["model_func"],
                parameters=parameters,
                fit_domain=tab["fit_domain"],
                use_fit_domain=bool(tab["use_fit_domain"]),
                best_fit=bool(tab["saved_fit"]),
            )
        )
    return plots
