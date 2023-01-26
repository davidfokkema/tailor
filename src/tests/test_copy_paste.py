import sys

sys.path.append("src/")


import IPython
import numpy as np
import pandas as pd
from PySide6 import QtCore, QtWidgets

from tailor.app import Application

SELECT = QtCore.QItemSelectionModel.SelectionFlag.Select
TOGGLE = QtCore.QItemSelectionModel.SelectionFlag.Toggle


def test_copy_paste():
    qapp = QtWidgets.QApplication()
    app = Application()

    x = np.arange(20)
    app.data_model.beginResetModel()
    app.data_model._data = pd.DataFrame.from_dict(
        {"x": x, "y": x**2, "z": x / 2, "a": x * 2, "b": np.sin(x)}
    )
    app.data_model.endResetModel()

    app.ui.show()

    set_selection(app, 1, 1, 3, 8, SELECT)
    set_selection(app, 2, 2, 2, 4, TOGGLE)
    set_selection(app, 4, 9, 4, 9, SELECT)
    app.copy_selected_cells()

    text = """\
1.0	0.5	2.0	
4.0		4.0	
9.0		6.0	
16.0		8.0	
25.0	2.5	10.0	
36.0	3.0	12.0	
49.0	3.5	14.0	
64.0	4.0	16.0	
			0.4121184852"""
    assert app.clipboard.text() == text

    app.ui.data_view.setCurrentIndex(app.data_model.createIndex(3, 0))

    app.paste_cells()

    # IPython.embed()

    qapp.exec()


def set_selection(app, x1, y1, x2, y2, flag):
    app.selection.select(
        QtCore.QItemSelection(
            app.data_model.createIndex(y1, x1),
            app.data_model.createIndex(y2, x2),
        ),
        flag,
    )


if __name__ == "__main__":
    test_copy_paste()
