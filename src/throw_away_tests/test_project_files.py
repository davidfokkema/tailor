import sys

sys.path.append("src/")

import numpy as np
import pandas as pd
from PySide6 import QtCore, QtWidgets

from tailor import project_files
from tailor.app import Application
from tailor.data_sheet import DataSheet
from tailor.plot_tab import PlotTab


def create_test_project(app: Application):
    # set up data
    sheet: DataSheet = app.ui.tabWidget.widget(0)
    sheet.data_model.removeColumn(1)
    sheet.data_model.insertCalculatedColumn(1)
    sheet.data_model.insertCalculatedColumn(2)
    sheet.data_model.insertCalculatedColumn(3)
    sheet.data_model.renameColumn(0, "x")
    sheet.data_model.renameColumn(1, "y")
    sheet.data_model.renameColumn(2, "z")
    sheet.data_model.renameColumn(3, "t")
    # sheet.data_model.insertRows(0, 5)
    sheet.data_model.setDataFromArray(
        sheet.data_model.createIndex(0, 0),
        values=np.linspace(0, np.pi, 10).reshape((10, 1)),
    )
    sheet.data_model.updateColumnExpression(1, "sin(x)")
    sheet.data_model.updateColumnExpression(3, "y")
    sheet.data_model.updateColumnExpression(3, "y * a")

    # create plot
    x_col = sheet.data_model.columnLabel(0)
    y_col = sheet.data_model.columnLabel(1)
    app.create_plot_tab(sheet, x_col, y_col, None, None)

    plottab: PlotTab = app.ui.tabWidget.currentWidget()
    plottab.ui.model_func.setPlainText("a * (x + x0) **2 + b")
    plottab.ui.fit_start_box.setValue(1.0)
    plottab.ui.fit_end_box.setValue(3.0)
    plottab.ui.use_fit_domain.setCheckState(QtCore.Qt.CheckState.Checked)
    plottab.ui.draw_curve_option.setCurrentIndex(2)
    plottab._params["a"].findChild(QtWidgets.QWidget, "value").setValue(2.0)
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

    app.ui.tabWidget.setCurrentWidget(plottab)


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = Application(add_sheet=True)

    create_test_project(app)
    model = project_files.save_project_to_json(app)

    app = Application()
    project_files.load_project_from_json(app, model)

    app.show()
    qapp.exec()
    qapp.quit()