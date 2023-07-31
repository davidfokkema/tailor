import sys

from tailor.data_sheet import DataSheet
from tailor.project_models import Parameter, Plot, Project, Sheet


def load_legacy_project(jsondict: dict) -> Project:
    try:
        data = jsondict["data_model"]["data"]
        col_expressions = {
            k: v if v is not None else ""
            for k, v in jsondict["data_model"]["calculated_columns"].items()
        }
        sheet = Sheet(
            name="Sheet 1",
            id=1,
            data=data,
            new_col_num=jsondict["data_model"]["new_col_num"],
            col_names={k: k for k in data.keys()},
            calculated_column_expression=col_expressions,
            is_calculated_column_valid={k: False for k in data.keys()},
        )
        project = Project(
            application=jsondict["application"],
            version=jsondict["version"],
            sheet_num=2,
            plot_num=2,
            tabs=[sheet],
            current_tab=jsondict["current_tab"],
        )
        return project
    except Exception as exc:
        print(exc)
        sys.exit()


def fix_legacy_project(project):
    # force checking if calculated columns are valid
    for tab in [
        project.ui.tabWidget.widget(idx) for idx in range(project.ui.tabWidget.count())
    ]:
        if isinstance(tab, DataSheet):
            tab.data_model._data.recalculate_all_columns()
