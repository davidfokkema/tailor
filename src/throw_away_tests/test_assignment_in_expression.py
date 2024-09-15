import sys

sys.path.append("src/")

import numpy as np
import pandas as pd
from PySide6 import QtCore, QtWidgets

from tailor.app import MainWindow
from tailor.data_sheet import DataSheet
from tailor.plot_tab import PlotTab


def create_test_project(app: MainWindow):
    # set up data
    sheet: DataSheet = app.ui.tabWidget.widget(0)
    sheet.model.insertCalculatedColumn(2)
    sheet.model.updateColumnExpression(2, "y = 4")

    sheet.ui.data_view.setCurrentIndex(sheet.model.createIndex(0, 2))
    sheet.ui.formula_edit.setFocus()


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = MainWindow(add_sheet=True)

    create_test_project(app)
    app.mark_project_dirty(False)

    app.show()
    qapp.exec()
    qapp.quit()
