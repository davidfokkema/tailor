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
    app.create_plot_tab(sheet1, "t", "y")

    plot1 = app.ui.tabWidget.currentWidget()
    plot1.ui.model_func.setPlainText("a * t + b")
    plot1.perform_fit()


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = Application()

    test_sheets_and_columns(app)

    app.show()
    qapp.exec()

    qapp.quit()
