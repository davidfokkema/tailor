import sys

sys.path.append("src/")

import numpy as np
import pandas as pd
from PySide6 import QtWidgets

from tailor.app import Application


def test_plot_tab(app: Application):
    x = np.arange(20)
    app.data_model.beginResetModel()
    app.data_model._data = pd.DataFrame.from_dict({"x": x, "y": x**2})
    app.data_model.endResetModel()

    app.create_plot_tab("x", "y")
    plottab = app.ui.tabWidget.currentWidget()
    plottab.model_func.setPlainText("a * x**2 + b * x + c + d + f + g")


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = Application()

    test_plot_tab(app)

    app.ui.show()
    qapp.exec()

    qapp.quit()
