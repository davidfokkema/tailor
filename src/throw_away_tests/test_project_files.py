import sys

sys.path.append("src/")

import numpy as np
import pandas as pd
from PySide6 import QtWidgets

from tailor import project_files
from tailor.app import Application
from tailor.data_sheet import DataSheet
from tailor.plot_tab import PlotTab


def create_test_project(app: Application):
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

    plottab: PlotTab = app.ui.tabWidget.currentWidget()
    plottab.ui.model_func.setPlainText("a * (x + x0) **2 + b")
    plottab.perform_fit()

    # create new sheet
    sheet2 = app.add_data_sheet()
    sheet2.data_model.renameColumn(0, "x")
    sheet2.data_model.renameColumn(1, "sinx")
    x = np.linspace(0, 3 * np.pi, 15)
    sheet2.data_model.setDataFromArray(
        sheet2.data_model.createIndex(0, 0), values=np.array((x, np.sin(x))).T
    )
    x_col = sheet2.data_model.columnLabel(0)
    y_col = sheet2.data_model.columnLabel(1)
    app.create_plot_tab(sheet2, x_col, y_col, None, None)


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = Application()

    create_test_project(app)
    model = project_files.save_project(app)
    print(f"{model}")

    # app.show()
    # qapp.exec()

    # qapp.quit()
