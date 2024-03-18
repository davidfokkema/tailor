import sys

sys.path.append("src/")

import numpy as np
from PySide6 import QtCore, QtWidgets

from tailor.app import MainWindow
from tailor.data_sheet import DataSheet
from tailor.plot_tab import PlotTab


def create_test_project(app: MainWindow):
    # set up data
    sheet: DataSheet = app.ui.tabWidget.widget(0)
    x = np.linspace(0, 10, 11)
    sheet.model.setDataFromArray(
        sheet.model.createIndex(0, 0),
        values=np.array([x, 2 * x + 3]).T,
    )

    # create plot
    x_col = sheet.model.columnLabel(0)
    y_col = sheet.model.columnLabel(1)
    app.create_plot_tab(sheet, x_col, y_col, None, y_col)

    plot1: PlotTab = app.ui.tabWidget.currentWidget()
    plot1.ui.model_func.setPlainText("a * x +b")
    plot1.ui.draw_curve_option.setCurrentIndex(1)
    plot1.perform_fit()


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = MainWindow(add_sheet=True)

    create_test_project(app)
    app.mark_project_dirty(False)

    app.show()
    qapp.exec()
    qapp.quit()
