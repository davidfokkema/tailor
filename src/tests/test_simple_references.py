import sys

sys.path.append("src/")


import numpy as np
import pandas as pd
from PySide6 import QtCore, QtWidgets

from tailor.app import Application


def test_move_column(app: Application):
    x = np.arange(20)
    sheet1 = app.ui.tabWidget.currentWidget()
    sheet1.data_model.beginResetModel()
    sheet1.data_model._data = pd.DataFrame.from_dict(
        {"x": x, "y": x**2, "z": x / 2, "a": x * 2, "b": np.sin(x)}
    )
    sheet1.data_model.endResetModel()
    sheet1.add_calculated_column()
    sheet1.rename_column("func1")
    sheet1.ui.formula_edit.setText("y ** 2")
    sheet1.update_column_expression("y ** 2")

    sheet1.ui.data_view.horizontalHeader().moveSection(1, 3)

    app.create_plot_tab(sheet1, "x", "y")

    app.ui.tabWidget.setCurrentIndex(0)
    sheet1.rename_column("newy")
    app.ui.tabWidget.setCurrentIndex(1)

    plot1 = app.ui.tabWidget.currentWidget()
    plot1.ui.model_func.setPlainText("a * x**2 + b * x")
    plot1.perform_fit()


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = Application()

    test_move_column(app)

    app.show()
    qapp.exec()

    qapp.quit()
