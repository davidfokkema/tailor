import sys

sys.path.append("src/")

import numpy as np
import pandas as pd
from PySide6 import QtWidgets

from tailor.app import Application
from tailor.data_sheet import DataSheet


def test_plot_tab(app: Application):
    # set up data
    sheet: DataSheet = app.ui.tabWidget.widget(0)
    sheet.data_model.removeColumn(1)
    sheet.data_model.insertCalculatedColumn(1)
    sheet.data_model.renameColumn(0, "x")
    sheet.data_model.renameColumn(1, "y")
    sheet.data_model.insertRows(0, 5)
    sheet.data_model.setDataFromArray(
        sheet.data_model.createIndex(0, 0),
        values=np.linspace(0, np.pi, 10).reshape((10, 1)),
    )
    sheet.data_model.updateColumnExpression(1, "sin(x)")

    # create plot
    x_col = sheet.data_model.columnLabel(0)
    y_col = sheet.data_model.columnLabel(1)
    app.create_plot_tab(sheet, x_col, y_col, None, None)

    plottab = app.ui.tabWidget.currentWidget()
    plottab.ui.model_func.setPlainText("a * x**2 + b")


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = Application()

    test_plot_tab(app)

    app.show()
    qapp.exec()

    qapp.quit()
