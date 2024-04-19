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
    sheet.model.removeColumn(1)
    sheet.model.insertCalculatedColumn(1)
    sheet.model.insertCalculatedColumn(2)
    sheet.model.insertCalculatedColumn(3)
    sheet.model.renameColumn(0, "x")
    sheet.model.renameColumn(1, "y")
    sheet.model.renameColumn(2, "z")
    sheet.model.renameColumn(3, "t")
    sheet.model.setDataFromArray(
        sheet.model.createIndex(0, 0),
        values=np.linspace(0, np.pi, 50000).reshape((50000, 1)),
    )
    sheet.model.updateColumnExpression(1, "sin(x)")
    sheet.model.updateColumnExpression(3, "y")
    sheet.model.updateColumnExpression(3, "y * a")

    sheet.ui.data_view.setCurrentIndex(sheet.model.createIndex(0, 1))
    sheet.ui.formula_edit.setFocus()


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = MainWindow(add_sheet=True)

    create_test_project(app)
    app.mark_project_dirty(False)

    app.show()
    qapp.exec()
    qapp.quit()
