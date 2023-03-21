import sys

sys.path.append("src/")


import numpy as np
import pandas as pd
from PySide6 import QtCore, QtWidgets

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
    app.create_plot_tab(sheet2, "t", "s")

    # WIP
    # make plots aware of data_model's origin sheet
    # only update plots with data from current sheet
    # only rename columns for plots with data from current sheet


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = Application()

    test_sheets_and_columns(app)

    app.show()
    qapp.exec()

    qapp.quit()
