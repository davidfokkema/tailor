import sys

sys.path.append("src/")

import pathlib
import tempfile

import numpy as np
import pandas as pd
from PySide6 import QtWidgets

from tailor.app import Application


def test_sheets_and_columns(app: Application):
    x = np.arange(20)
    sheet1 = app.ui.tabWidget.currentWidget()
    sheet1.data_model.beginResetModel()
    sheet1.data_model._data = pd.DataFrame.from_dict(
        {"t": x, "y": x**2, "z": x / 2, "a": x * 2, "b": np.sin(x)}
    )
    sheet1.data_model.endResetModel()
    app.create_plot_tab(sheet1, "t", "b")

    sheet2 = app.add_data_sheet()
    t = np.arange(10)
    sheet2.data_model.beginResetModel()
    sheet2.data_model._data = pd.DataFrame.from_dict({"t": t, "s": 2 * t + 3})
    sheet2.data_model.endResetModel()
    plot2 = app.create_plot_tab(sheet2, "t", "s")

    # Rename column
    app.ui.tabWidget.setCurrentWidget(sheet1)
    sheet1.ui.data_view.setCurrentIndex(sheet1.data_model.createIndex(0, 0))
    sheet1.rename_column("time")

    # column must not be renamed to 'time', but still be 't'
    app.ui.tabWidget.setCurrentIndex(3)
    assert plot2.x_var == "t"

    # duplicate a data sheet
    app.ui.tabWidget.setCurrentWidget(sheet1)
    app.duplicate_data_sheet()

    # export and import CSV
    with tempfile.TemporaryDirectory() as dirname:
        path = pathlib.Path(dirname) / "test.csv"
        app._do_export_csv(sheet1, path)
        new_sheet = app.add_data_sheet()
        app._do_import_csv(
            new_sheet,
            path,
            delimiter=",",
            decimal=".",
            thousands=None,
            header=0,
            skiprows=0,
        )
        # import into another sheet
        app.ui.tabWidget.setCurrentWidget(sheet2)
        app._do_import_csv(
            sheet2,
            path,
            delimiter=",",
            decimal=".",
            thousands=None,
            header=0,
            skiprows=0,
        )


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = Application()

    test_sheets_and_columns(app)

    app.show()
    qapp.exec()

    qapp.quit()
